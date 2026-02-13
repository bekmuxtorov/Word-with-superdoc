<script setup>
import '@superdoc/common/styles/common-styles.css';
import '../dev-styles.css';
import { nextTick, onMounted, onBeforeUnmount, provide, ref, shallowRef, computed } from 'vue';

import { SuperDoc } from '@superdoc/index.js';
import { DOCX, PDF, HTML } from '@superdoc/common';
import { getFileObject } from '@superdoc/common';
import BasicUpload from '@superdoc/common/components/BasicUpload.vue';
import SuperdocLogo from './superdoc-logo.webp?url';
import { fieldAnnotationHelpers } from '@superdoc/super-editor';
import { toolbarIcons } from '../../../../super-editor/src/components/toolbar/toolbarIcons';
import BlankDOCX from '@superdoc/common/data/blank.docx?url';
import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import * as pdfjsViewer from 'pdfjs-dist/web/pdf_viewer.mjs';
import { getWorkerSrcFromCDN } from '../../components/PdfViewer/pdf/pdf-adapter.js';
import SidebarSearch from './sidebar/SidebarSearch.vue';
import SidebarFieldAnnotations from './sidebar/SidebarFieldAnnotations.vue';
import { HocuspocusProvider } from '@hocuspocus/provider';
import * as Y from 'yjs';
import QRCodeImage from '../../assets/qr.png';

// note:
// Or set worker globally outside the component.
// pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
//   'pdfjs-dist/build/pdf.worker.min.mjs',
//   import.meta.url,
// ).toString();

/* For local dev */
const superdoc = shallowRef(null);
const activeEditor = shallowRef(null);

const title = ref('initial title');
const currentFile = ref(null);
const commentsPanel = ref(null);
const showCommentsPanel = ref(true);
const sidebarInstanceKey = ref(0);

const urlParams = new URLSearchParams(window.location.search);
const isInternal = urlParams.has('internal');
const testUserEmail = urlParams.get('email') || 'user@superdoc.com';
const testUserName = urlParams.get('name') || `SuperDoc ${Math.floor(1000 + Math.random() * 9000)}`;
const userRole = urlParams.get('role') || 'editor';
const useLayoutEngine = ref(urlParams.get('layout') !== '0');
const useWebLayout = ref(urlParams.get('view') === 'web');
const useCollaboration = urlParams.get('collab') === '1';

// Collaboration state
const ydocRef = shallowRef(null);
const providerRef = shallowRef(null);
const collabReady = ref(false);
const superdocLogo = SuperdocLogo;
const uploadedFileName = ref('');
const uploadDisplayName = computed(() => uploadedFileName.value || 'No file chosen');
const isDragging = ref(false);
const isMoreMenuOpen = ref(false);

const handleDragOver = (e) => {
  // Only handle file drags from OS
  if (e.dataTransfer?.types && Array.from(e.dataTransfer.types).includes('Files')) {
    isDragging.value = true;
  }
};

const handleDragLeave = (e) => {
  // Don't hide if moving to a child element
  if (e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) {
    return;
  }
  isDragging.value = false;
};

const handleDrop = async (e) => {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    await handleNewFile(files[0]);
  }
};

// URL loading
const documentUrl = ref('');
const isLoadingUrl = ref(false);

const getToken = () => {
  const urlToken = urlParams.get('token');
  // Fallback token (from original code) if not provided in URL
  const defaultToken =
    'ew0KImFsZyI6ICJIUzI1NiIsDQoidHlwIjogIkpXVCINCn0.ew0KInVzZXJHVUlEIjogIjBmYTVhOWI5LWIzMGItMTFmMC1hZGJmLTI0NGJmZTkzYmEyMyIsDQoiaXNzIjogIkVLT01QTEVLVEFTSVlBIiwNCiJ1bml2ZXJzYWxEYXRlIjogIjIwMjYtMDEtMTJUMDg6MDg6NTYiLA0KImV4cCI6IDE3NzA3OTczMzYsDQoic3ViIjogIldvcmQiLA0KImF1ZCI6ICJqd3RBdXRoIiwNCiJuYmYiOiAxNzY4MjA1MzM2LA0KImlhdCI6IDE3NjgyMDUzMzYNCn0.6tPhT49hdFxWVtmWRERR19mMPZgzzqPtPO_Hj3DI-m4';
  return urlToken || defaultToken;
};

const handleInsertQRCode = async () => {
  if (!activeEditor.value) return;
  
  const editor = activeEditor.value;
  const docSize = editor.state.doc.content.size;
  
  // Create a new paragraph at the end if needed, or just insert the image
  // We set selection to end of doc
  // editor.commands.setTextSelection({ from: docSize });
  
  console.log('Schema nodes:', Object.keys(editor.state.schema.nodes));
  
  try {
    // Convert QR code to base64 because imageRegistrationPlugin only accepts:
    // - http/https URLs
    // - data: URIs (base64)
    // It does NOT accept relative paths like /src/assets/qr.png
    const qrUrl = new URL(QRCodeImage, window.location.origin).href;
    console.log('Fetching QR from:', qrUrl);
    
    const response = await fetch(qrUrl);
    if (!response.ok) throw new Error(`Failed to fetch image: ${response.status}`);
    
    const blob = await response.blob();
    const base64QR = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
    
    console.log('Converted QR to base64, length:', base64QR.length);

    const imageNode = editor.schema.nodes.image.create({
      src: base64QR,
      alt: 'QR Code',
      title: '{{qrcode}}',
      ignoreRegistration: true, // Bypass browser imageRegistrationPlugin
      size: {
        width: 100,
        height: 100
      }
    });
    
    console.log('Created image node with base64 QR');
    
    const paragraphNode = editor.schema.nodes.paragraph.create(null, imageNode);

    // Insert QR code image at the end of the document
    // We use a transaction to insert the node directly
    const tr = editor.state.tr.insert(docSize, paragraphNode);
    editor.view.dispatch(tr);
    
    console.log('Dispatch complete');
    
    // Scroll
    if (editor.view && editor.view.dom) {
      editor.view.dom.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  } catch (e) {
    console.error('Error creating/inserting node:', e);
  }


};

const handleLoadFromUrl = async () => {
  const url = documentUrl.value.trim();
  if (!url) return;

  isLoadingUrl.value = true;
  try {
    const token = getToken();
    // Use manual fetch to include authorization header
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    // Create a File object from the blob to mimic getFileObject result
    const file = new File([blob], 'document.docx', { type: DOCX });

    await handleNewFile(file);
  } catch (err) {
    console.error('Failed to load from URL:', err);
    const message = err instanceof Error ? err.message : String(err);
    alert(`Failed to load document: ${message}`);
  } finally {
    isLoadingUrl.value = false;
  }
};

const user = {
  name: testUserName,
  email: testUserEmail,
};

const commentPermissionResolver = ({ permission, comment, defaultDecision, currentUser }) => {
  if (!comment) return defaultDecision;

  // Example: hide tracked-change buttons for matching author email domain
  if (
    comment.trackedChange &&
    comment.creatorEmail?.endsWith('@example.com') &&
    ['RESOLVE_OWN', 'REJECT_OWN'].includes(permission)
  ) {
    return false;
  }

  // Allow default behaviour for everything else
  return defaultDecision;
};

const handleNewFile = async (file) => {
  uploadedFileName.value = file?.name || '';
  // Generate a file url
  const url = URL.createObjectURL(file);

  // Detect file type by extension
  const fileExtension = file.name.split('.').pop()?.toLowerCase();
  const isMarkdown = fileExtension === 'md';
  const isHtml = fileExtension === 'html' || fileExtension === 'htm';

  if (isMarkdown || isHtml) {
    // For text-based files, read the content and use a blank DOCX as base
    const content = await readFileAsText(file);
    currentFile.value = await getFileObject(BlankDOCX, 'blank.docx', DOCX);

    // Store the content to be passed to SuperDoc
    if (isMarkdown) {
      currentFile.value.markdownContent = content;
    } else if (isHtml) {
      currentFile.value.htmlContent = content;
    }
  } else {
    // For binary files (DOCX, PDF), use as-is
    currentFile.value = await getFileObject(url, file.name, file.type);
  }

  nextTick(() => {
    init();
  });

  sidebarInstanceKey.value += 1;
};

/**
 * Read a file as text content
 * @param {File} file - The file to read
 * @returns {Promise<string>} The file content as text
 */
const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
};

const init = async () => {
  // If the dev shell re-initializes (e.g. on file upload), tear down the previous instance first.
  superdoc.value?.destroy?.();
  superdoc.value = null;
  activeEditor.value = null;

  let testId = 'document-123';

  // eslint-disable-next-line no-unused-vars
  const testDocumentId = 'doc123';

  // Prepare document config only if a file was uploaded
  // If no file, SuperDoc will automatically create a blank document
  let documentConfig = null;
  if (currentFile.value) {
    documentConfig = {
      data: currentFile.value,
      id: testId,
    };

    // Add markdown/HTML content if present
    if (currentFile.value.markdownContent) {
      documentConfig.markdown = currentFile.value.markdownContent;
    }
    if (currentFile.value.htmlContent) {
      documentConfig.html = currentFile.value.htmlContent;
    }
  }

  const config = {
    superdocId: 'superdoc-dev',
    selector: '#superdoc',
    toolbar: 'toolbar',
    toolbarGroups: ['center'],
    role: userRole,
    documentMode: 'editing',
    licenseKey: 'public_license_key_superdocinternal_ad7035140c4b',
    telemetry: {
      enabled: true,
      metadata: {
        source: 'superdoc-dev'
      }
    },
    comments: {
      visible: true,
    },
    trackChanges: {
      visible: true,
    },
    toolbarGroups: ['left', 'center', 'right'],
    pagination: useLayoutEngine.value && !useWebLayout.value,
    viewOptions: { layout: useWebLayout.value ? 'web' : 'print' },
    // Web layout mode requires Layout Engine to be OFF (uses ProseMirror's native rendering)
    useLayoutEngine: useLayoutEngine.value && !useWebLayout.value,
    rulers: true,
    rulerContainer: '#ruler-container',
    annotations: true,
    isInternal,
    // disableContextMenu: true,
    // format: 'docx',
    // html: '<p>Hello world</p>',
    // isDev: true,
    user,
    title: 'Test document',
    users: [
      { name: 'Nick Bernal', email: 'nick@harbourshare.com', access: 'internal' },
      { name: 'Eric Doversberger', email: 'eric@harbourshare.com', access: 'external' },
    ],
    // Only pass document config if a file was uploaded, otherwise SuperDoc creates blank
    ...(documentConfig ? { document: documentConfig } : {}),
    // documents: [
    //   {
    //     data: currentFile.value,
    //     id: testId,
    //   },
    // ],
    // cspNonce: 'testnonce123',
    modules: {
      comments: {
        // comments: sampleComments,
        // overflow: true,
        // selector: 'comments-panel',
        // useInternalExternalComments: true,
        // suppressInternalExternal: true,
        permissionResolver: commentPermissionResolver,
      },
      toolbar: {
        selector: 'toolbar',
        toolbarGroups: ['left', 'center', 'right'],
        // groups: {
        //   center: ['bold'],
        //   right: ['documentMode']
        // },
        // fonts: null,
        // hideButtons: false,
        // responsiveToContainer: true,
        excludeItems: [], // ['italic', 'bold'],
        // texts: {},
      },
      // Test custom slash menu configuration
      slashMenu: {
        // includeDefaultItems: true, // Include default items
        // customItems: [
        //   {
        //     id: 'custom-section',
        //     items: [
        //       {
        //         id: 'show-context',
        //         label: 'Show Context',
        //         showWhen: (context) => context.trigger === 'click',
        //         render: (context) => {
        //           const container = document.createElement('div');
        //           container.style.display = 'flex';
        //           container.style.alignItems = 'center';
        //           container.innerHTML = `
        //             <span style="margin-right: 8px;">🔍</span>
        //             <span>Show Context</span>
        //           `;
        //           return container;
        //         },
        //         action: (editor, context) => {
        //           console.log('context', context);
        //         }
        //       },
        //       {
        //         id:'delete table',
        //         label: 'Delete Table',
        //         render: (context) => {
        //           const container = document.createElement('div');
        //           container.style.display = 'flex';
        //           container.style.alignItems = 'center';
        //           container.innerHTML = `
        //             <span style="margin-right: 8px;">🗑️</span>
        //             <span>Delete Table</span>
        //           `;
        //           return container;
        //         },
        //         action: (editor) => {
        //           editor.commands.deleteTable();
        //         },
        //         showWhen: (context) => context.isInTable
        //       },
        //       {
        //         id: 'highlight-text',
        //         label: 'Highlight Selection',
        //         showWhen: (context) => ['slash', 'click'].includes(context.trigger),
        //         render: (context) => {
        //           const container = document.createElement('div');
        //           container.style.display = 'flex';
        //           container.style.alignItems = 'center';
        //           container.innerHTML = `
        //             <span style="margin-right: 8px; color: #ffa500;">✨</span>
        //             <span>Highlight "${context.selectedText || 'text'}"</span>
        //           `;
        //           return container;
        //         },
        //         action: (editor) => {
        //           editor.commands.setHighlight('#ffff00');
        //         },
        //         showWhen: (context) => context.hasSelection
        //       },
        //       {
        //         id: 'insert-emoji',
        //         label: 'Insert Emoji',
        //         showWhen: (context) => (context.trigger === 'click' || context.trigger === 'slash') && context.hasSelection,
        //         render: (context) => {
        //           const container = document.createElement('div');
        //           container.style.display = 'flex';
        //           container.style.alignItems = 'center';
        //           container.innerHTML = `
        //             <span style="margin-right: 8px;">😀</span>
        //             <span>Insert Emoji</span>
        //           `;
        //           return container;
        //         },
        //         action: (editor) => {
        //           editor.commands.insertContent('¯\\_(ツ)_/¯');
        //         }
        //       },
        //     ]
        //   }
        // ],
        // // Alternative: use menuProvider function
        // // @todo: decide if we want to expose this in the documentation or not for simplicity?
        // menuProvider: (context, defaultSections) => {
        //   return [
        //     ...defaultSections,
        //     {
        //       id: 'dynamic-section',
        //       items: [
        //         {
        //           id: 'dynamic-item',
        //           label: `Custom for ${context.documentMode}`,
        //           showWhen: (context) => ['slash', 'click'].includes(context.trigger),
        //           action: (editor) => {
        //             editor.commands.insertContent(`Mode: ${context.documentMode} `);
        //           }
        //         }
        //       ]
        //     }
        //   ];
        // }
      },
      // 'hrbr-fields': {},

      // Collaboration - enabled via ?collab=1 URL param
      // Run `pnpm run collab-server` first, then open http://localhost:5173?collab=1
      ...(useCollaboration && ydocRef.value && providerRef.value
        ? {
            collaboration: {
              ydoc: ydocRef.value,
              provider: providerRef.value,
            },
          }
        : {}),
      ai: {
        // Provide your Harbour API key here for direct endpoint access
        // apiKey: 'test',
        // Optional: Provide a custom endpoint for AI services
        // endpoint: 'https://sd-dev-express-gateway-i6xtm.ondigitalocean.app/insights',
      },
      pdf: {
        pdfLib: pdfjsLib,
        pdfViewer: pdfjsViewer,
        setWorker: true,
        workerSrc: getWorkerSrcFromCDN(pdfjsLib.version),
        textLayerMode: 0,
      },
      whiteboard: {
        enabled: false,
      },
    },
    onEditorCreate,
    onContentError,
    // handleImageUpload: async (file) => url,
    // Override icons.
    toolbarIcons: {},
    onCommentsUpdate,
    onCommentsListChange: ({ isRendered }) => {
      isCommentsListOpen.value = isRendered;
    },
  };

  superdoc.value = new SuperDoc(config);
  superdoc.value?.on('ready', () => {
    superdoc.value.addCommentsList(commentsPanel.value);
  });
  superdoc.value?.on('exception', (error) => {
    console.error('SuperDoc exception:', error);
  });

  window.superdoc = superdoc.value;

  // const ydoc = superdoc.value.ydoc;
  // const metaMap = ydoc.getMap('meta');
  // metaMap.observe((event) => {
  //   const { keysChanged } = event;
  //   keysChanged.forEach((key) => {
  //     if (key === 'title') {
  //       title.value = metaMap.get('title');
  //     }
  //   });
  // });
};

const onCommentsUpdate = () => {};

const onContentError = ({ editor, error, documentId, file }) => {
  console.debug('Content error on', documentId, error);
};

const isSending = ref(false);

const handleSendFile = async () => {
  if (isSending.value) return;

  // Attempt to get 'id' from the manual URL input first, then URL params
  let id = null;
  const urlInputValue = documentUrl.value.trim();

  // Regex to match /files/<id>/content
  // Supports common patterns like:
  // http://.../api/files/123/content
  // /api/files/123/content/
  const idMatch = urlInputValue.match(/\/files\/(\d+)\/content/);
  if (idMatch && idMatch[1]) {
    id = idMatch[1];
  } else {
    // Fallback to URL query param
    id = urlParams.get('id');
  }

  const token = getToken();

  if (!id) {
    alert(
      "Fayl ID si topilmadi! Iltimos, 'Load URL' maydoniga to'g'ri URL kiriting (masalan: .../api/files/1/content).",
    );
    return;
  }

  // Construct Server URL using the extracted ID
  // User requested: /api/files/<id>/content/
  // Assuming relative path if on same domain or absolute if needed.
  // Since the user provided http://127.0.0.1:8000/api/files/1/content in example, we should probably check if we need a full domain or just the path.
  // However, the previous code used https://ekomplektasiya.uz/Xujjatlar/upload/${id}
  // The user explicitly asked for: /api/files/<id>/content/
  // We will use the base from the input if possible, or construct it.

  // Let's construct the target URL.
  // If the user input contained the full URL, we might want to use that base?
  // But the user request said: "http://127.0.0.1:8000/api/files/1/content dagi id olinsin" AND "yuqoridagi apiga fayl yuborilishini ta'minlab ber"
  // So the target URL is exactly what they typed (or the pattern matches).

  // A safe bet is to use the ID to construct the URL as requested:
  // http://127.0.0.1:8000/api/files/<id>/content/
  // But wait, hardcoding localhost might be bad if deployed.
  // Use the input URL origin if available or fall back to current origin + path.

  // Ideally, we just replace the ID in the pattern or construct it anew.
  // Let's assume the user wants to PUT to the SAME URL structure they loaded from (or similar).
  // The user said: "PUT /api/files/<id>/content/"

  const serverUrl = `http://127.0.0.1:8000/api/files/${id}/content/`;

  isSending.value = true;
  try {
    // Export document as blob
    const blob = await superdoc.value.export({ commentsType: 'external', triggerDownload: false });

    if (!blob || blob.size === 0) {
      alert("Fayl o'qilmadi yoki bo'sh.");
      return;
    }

    // Use FormData for file upload
    const formData = new FormData();
    formData.append('file', blob, 'document.docx'); // Assuming 'file' matches backend expectation

    const response = await fetch(serverUrl, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        // Do not set Content-Type for FormData, browser sets it with boundary automatically
        'Content-Disposition': 'attachment; filename="document.docx"', // Optional, helps with some parsers
      },
      body: formData,
    });

    if (response.status === 601) {
      alert("Xujjat imzolangan, uni o'zgartirish imkoni mavjud emas.");
    } else if (response.status === 403) {
      alert("Xujjatni o'zgartirish ruxsati sizda mavjud emas!");
    } else if (response.status >= 200 && response.status < 300) {
      alert('Xujjat fayli muaffaqiyatli yuborildi.');
    } else if (response.status >= 402) {
      const text = await response.text();
      alert(text);
    } else if (response.status >= 401) {
      alert('Fayl topilmadi yoki token eskirgan!');
    } else {
      const text = await response.text();
      alert(`❌ Xatolik! Status: ${response.status}\n${text}`);
    }
  } catch (err) {
    console.error('Send error:', err);
    alert(`Umumiy xatolik yuz berdi: ${err.message}`);
  } finally {
    isSending.value = false;
  }
};

const exportHTML = async (commentsType) => {
  console.debug('Exporting HTML', { commentsType });

  // Get HTML content from SuperDoc
  const htmlArray = superdoc.value.getHTML();
  const html = htmlArray.join('');

  // Create a Blob from the HTML
  const blob = new Blob([html], { type: 'text/html' });

  // Create a download link and trigger the download
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${title.value || 'document'}.html`;

  // Trigger the download
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up the URL
  URL.revokeObjectURL(url);

  console.debug('HTML exported successfully');
};

const exportDocx = async (commentsType) => {
  console.debug('Exporting docx', { commentsType });
  await superdoc.value.export({ commentsType });
};

const exportDocxBlob = async () => {
  const blob = await superdoc.value.export({ commentsType: 'external', triggerDownload: false });
  console.debug(blob);
};

const downloadBlob = (blob, fileName) => {
  if (!blob) return;
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const getActiveDocumentEntry = () => {
  const docsSource = superdoc.value?.superdocStore?.documents;
  const documents = Array.isArray(docsSource) ? docsSource : docsSource?.value;
  if (!documents?.length) return null;

  const activeDocId = activeEditor.value?.options?.documentId;
  if (activeDocId) {
    const activeDoc = documents.find((doc) => doc.id === activeDocId);
    if (activeDoc) return activeDoc;
  }

  return documents[0] ?? null;
};

const onEditorCreate = ({ editor }) => {
  activeEditor.value = editor;
  window.editor = editor;

  editor.on('fieldAnnotationClicked', (params) => {
    console.log('fieldAnnotationClicked', { params });
  });

  editor.on('fieldAnnotationSelected', (params) => {
    console.log('fieldAnnotationSelected', { params });
  });

  editor.on('fieldAnnotationDoubleClicked', (params) => {
    console.log('fieldAnnotationDoubleClicked', { params });
  });
};

const handleTitleChange = (e) => {
  title.value = e.target.innerText;

  const ydoc = superdoc.value.ydoc;
  const metaMap = ydoc.getMap('meta');
  metaMap.set('title', title.value);
  console.debug('Title changed', metaMap.toJSON());
};

const isCommentsListOpen = ref(false);
const toggleCommentsPanel = () => {
  if (isCommentsListOpen.value) {
    superdoc.value?.removeCommentsList();
  } else {
    superdoc.value?.addCommentsList(commentsPanel.value);
  }
};

onMounted(async () => {
  // Initialize collaboration if enabled via ?collab=1
  if (useCollaboration) {
    const ydoc = new Y.Doc();
    const provider = new HocuspocusProvider({
      url: 'ws://localhost:3050',
      name: 'superdoc-dev-room',
      document: ydoc,
    });

    ydocRef.value = ydoc;
    providerRef.value = provider;

    // Wait for sync before loading document
    await new Promise((resolve) => {
      provider.on('synced', () => {
        collabReady.value = true;
        resolve();
      });
      // Fallback timeout in case sync doesn't fire
      setTimeout(() => {
        collabReady.value = true;
        resolve();
      }, 3000);
    });

    console.log('[collab] Provider synced, initializing SuperDoc');
  }

  const urlParam = urlParams.get('url');
  const idParam = urlParams.get('id');

  if (idParam) {
    // Priority 1: Load by ID
    documentUrl.value = `https://ekomplektasiya.uz/Xujjatlar/${idParam}`;
    await handleLoadFromUrl();
  } else if (urlParam) {
    // Priority 2: Load by explicit URL param
    documentUrl.value = urlParam;
    await handleLoadFromUrl();
  } else {
    // Fallback
    if (useCollaboration) {
      // If collaboration is active, just init (provider will sync doc)
      init();
    } else {
       // Default blank for non-collab
       const blankFile = await getFileObject(BlankDOCX, 'test.docx', DOCX);
       handleNewFile(blankFile);
    }
  }
});

onBeforeUnmount(() => {
  // Ensure SuperDoc tears down global listeners (e.g., PresentationEditor input bridge)
  superdoc.value?.destroy?.();
  superdoc.value = null;
  activeEditor.value = null;

  // Cleanup collaboration provider
  if (providerRef.value) {
    providerRef.value.destroy();
    providerRef.value = null;
  }
  ydocRef.value = null;
});

const toggleLayoutEngine = () => {
  const nextValue = !useLayoutEngine.value;
  const url = new URL(window.location.href);
  url.searchParams.set('layout', nextValue ? '1' : '0');
  window.location.href = url.toString();
};

const toggleViewLayout = () => {
  const nextValue = !useWebLayout.value;
  const url = new URL(window.location.href);
  url.searchParams.set('view', nextValue ? 'web' : 'print');
  window.location.href = url.toString();
};

const showExportMenu = ref(false);
const closeExportMenu = () => {
  showExportMenu.value = false;
};

const sidebarOptions = [
  {
    id: 'off',
    label: 'Off',
    component: null,
  },
  {
    id: 'search',
    label: 'Search',
    component: SidebarSearch,
  },
  {
    id: 'fields',
    label: 'Field Annotations',
    component: SidebarFieldAnnotations,
  },
];
const activeSidebarId = ref('off');
const activeSidebar = computed(
  () => sidebarOptions.find((option) => option.id === activeSidebarId.value) ?? sidebarOptions[0],
);
const activeSidebarComponent = computed(() => activeSidebar.value?.component ?? null);
const activeSidebarLabel = computed(() => activeSidebar.value?.label ?? 'None');
const showSidebarMenu = ref(false);
const closeSidebarMenu = () => {
  showSidebarMenu.value = false;
};
const setActiveSidebar = (id) => {
  activeSidebarId.value = id;
  closeSidebarMenu();
};

// Scroll test mode - adds content above editor to make page scrollable (for testing focus scroll bugs)
const scrollTestMode = ref(urlParams.get('scrolltest') === '1');
const toggleScrollTestMode = () => {
  const url = new URL(window.location.href);
  url.searchParams.set('scrolltest', scrollTestMode.value ? '0' : '1');
  window.location.href = url.toString();
};

// Debug: Track all scroll changes when in scroll test mode
if (scrollTestMode.value) {
  let lastScrollY = 0;
  window.addEventListener('scroll', () => {
    if (Math.abs(window.scrollY - lastScrollY) > 10) {
      console.log('[SCROLL-DEBUG] Scroll changed:', lastScrollY, '→', window.scrollY);
      console.trace('[SCROLL-DEBUG] Stack trace:');
      lastScrollY = window.scrollY;
    }
  });

  // Also intercept scrollTo calls
  const originalScrollTo = window.scrollTo.bind(window);
  window.scrollTo = function (...args) {
    console.log('[SCROLL-DEBUG] scrollTo called:', args);
    console.trace('[SCROLL-DEBUG] scrollTo stack:');
    return originalScrollTo(...args);
  };
}
</script>

<template>
  <div
    class="dev-app"
    :class="{ 'dev-app--scroll-test': scrollTestMode, 'dev-app--dragging': isDragging }"
    @drop.prevent="handleDrop"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
  >
    <div class="dev-app__layout">


      <!-- Spacer to push content down and make page scrollable (for testing focus scroll bugs) -->
      <div v-if="scrollTestMode" class="dev-app__scroll-test-spacer">
        <div class="dev-app__scroll-test-notice">
          <strong>⚠️ SCROLL TEST MODE</strong>
          <p>
            Scroll down to see the editor. This mode tests that clicking/typing in the editor doesn't cause page jumps.
          </p>
          <p>If clicking or typing causes the page to scroll back up here, the bug is present.</p>
        </div>
      </div>

      <div class="dev-app__toolbar-ruler-container">
        <div class="dev-app__toolbar-row">
          <div id="toolbar" class="sd-toolbar"></div>
    <div class="dev-app__toolbar-actions">
            <button class="dev-app__mini-btn" @click="handleInsertQRCode" title="QR Code qo'shish">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <path d="M3 14h7v7H3z"></path>
              </svg>
            </button>
            <div class="dev-app__more-menu-wrapper">
              <button class="dev-app__mini-btn dev-app__more-btn" @click="isMoreMenuOpen = !isMoreMenuOpen">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="1" />
                  <circle cx="12" cy="5" r="1" />
                  <circle cx="12" cy="19" r="1" />
                </svg>
              </button>
              <div v-if="isMoreMenuOpen" class="dev-app__more-menu">
                <div class="dev-app__menu-row">
                  <input
                    v-model="documentUrl"
                    type="text"
                    class="dev-app__mini-input"
                    placeholder="Load URL..."
                    @keydown.enter="handleLoadFromUrl"
                  />
                  <button class="dev-app__mini-btn" @click="handleLoadFromUrl" :disabled="isLoadingUrl">
                    Load
                  </button>
                </div>
                <div class="dev-app__menu-divider"></div>
                <button class="dev-app__menu-item" @click="exportDocx('external')">Saqlash</button>
                <button class="dev-app__menu-item" @click="handleSendFile" :disabled="isSending">
                  {{ isSending ? 'Yuborilmoqda...' : 'Yuborish' }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <div id="ruler-container" class="sd-ruler"></div>
      </div>

      <div class="dev-app__main">
        <div class="dev-app__view">
          <div class="dev-app__content">
            <div class="dev-app__content-container" :class="{ 'dev-app__content-container--web-layout': useWebLayout }">
              <div id="superdoc"></div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="activeSidebarComponent" class="dev-app__sidebar">
        <div class="dev-app__sidebar-content">
          <component
            :is="activeSidebarComponent"
            :key="`${activeSidebarId}-${sidebarInstanceKey}`"
            @close="setActiveSidebar('off')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.dev-app__toolbar-ruler-container {
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sd-toolbar {
  flex: 1;
  width: auto;
  min-width: 0; /* Allow shrinking below content size if needed */
  background: white;
  position: relative;
  z-index: 1;
}

.sd-ruler {
  display: flex;
  justify-content: center;
  background: #f5f5f5;
  border-top: 1px solid #e0e0e0;
  padding: 0;
  min-height: 25px;
}

/* Hide the ruler container when no ruler is rendered inside it */
.sd-ruler:not(:has(.ruler)) {
  display: none;
}

.comments-panel {
  width: 320px;
}

@media screen and (max-width: 1024px) {
  .superdoc {
    max-width: calc(100vw - 10px);
  }
}
</style>

<style scoped>
.temp-comment {
  margin: 5px;
  border: 1px solid black;
  display: flex;
  flex-direction: column;
}

.comments-panel {
  position: absolute;
  right: 0;
  height: 100%;
  background-color: #fafafa;
  z-index: 100;
}

.dev-app {
  background-color: #b9bfce;
  --header-height: 154px;
  --toolbar-height: 39px;

  width: 100%;
  height: 100vh;
}

.dev-app__layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden; /* Fix scrollbar issues */
}

.dev-app__toolbar-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  background: white;
  padding-right: 8px;
}

.dev-app__toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto; /* Push to right */
  padding-left: 8px;
  border-left: 1px solid #eee;
  height: 40px; /* Match toolbar height */
  flex-shrink: 0;
  z-index: 10;
}

.dev-app__mini-input {
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0 8px;
  font-size: 13px;
  width: 150px;
}

.dev-app__mini-btn {
  height: 28px;
  padding: 0 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dev-app__mini-btn:hover {
  background: #f5f5f5;
}

.dev-app__mini-btn--primary {
  background: #3b82f6;
  color: white;
  border: none;
}
.dev-app__mini-btn--primary:hover {
  background: #2563eb;
}

.dev-app__mini-btn--success {
  background: #10b981;
  color: white;
  border: none;
}
.dev-app__mini-btn--success:hover {
  background: #059669;
}




.dev-app__more-menu-wrapper {
  position: relative;
}

.dev-app__more-btn {
  padding: 0 8px;
  color: #64748b;
}

.dev-app__more-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 8px;
  min-width: 250px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dev-app__menu-row {
  display: flex;
  gap: 4px;
}

.dev-app__menu-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 0;
}

.dev-app__menu-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
  width: 100%;
}

.dev-app__menu-item:hover {
  background: #f8fafc;
}

.dev-app__main {
  display: flex;
  justify-content: center;
  overflow: auto;
  /* Test: creates a containing block for position:fixed elements (like context menu) */
  backdrop-filter: blur(0.5px);
}

.dev-app__sidebar {
  position: absolute;
  top: 0;
  right: 0;
  height: 100vh;
  width: 350px;
  max-width: 350px;
  background: #f8fafc;
  border-left: 1px solid rgba(15, 23, 42, 0.12);
  box-shadow: -12px 0 28px rgba(15, 23, 42, 0.2);
  z-index: 200;
  display: flex;
  flex-direction: column;
}

.dev-app__sidebar-content {
  flex: 1 1 auto;
  overflow: auto;
  padding: 16px;
}

.dev-app__view {
  display: flex;
  padding-top: 20px;
}

.dev-app__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.dev-app__content-container {
  width: auto;
}

/* Web layout mode: dev app container styling */
.dev-app__content-container--web-layout {
  width: 100%;
  max-width: 100%;
  padding: 0 16px;
  box-sizing: border-box;
  overflow-x: hidden;
}

/* Web layout mode: prevent centering to allow full-width layout */
.dev-app__content:has(.dev-app__content-container--web-layout) {
  align-items: stretch;
}

.dev-app__view:has(.dev-app__content-container--web-layout) {
  width: 100%;
}

.dev-app__main:has(.dev-app__content-container--web-layout) {
  overflow-x: hidden;
}

.dev-app__inputs-panel {
  display: grid;
  height: calc(100vh - var(--header-height) - var(--toolbar-height));
  background: #fff;
  border-right: 1px solid #dbdbdb;
}

.dev-app__inputs-panel-content {
  display: grid;
  overflow-y: auto;
  scrollbar-width: none;
}

/* Scroll Test Mode - makes page scrollable to test focus scroll bugs */
.dev-app--scroll-test {
  height: auto;
  min-height: 100vh;
}

.dev-app--scroll-test .dev-app__layout {
  height: auto;
  min-height: 100vh;
}

.dev-app--scroll-test .dev-app__main {
  overflow: visible;
}

.dev-app__scroll-test-spacer {
  height: 120vh;
  background: linear-gradient(180deg, #1e293b 0%, #334155 50%, #475569 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dev-app__scroll-test-notice {
  background: rgba(251, 191, 36, 0.15);
  border: 2px solid rgba(251, 191, 36, 0.5);
  border-radius: 12px;
  padding: 24px 32px;
  max-width: 500px;
  text-align: center;
  color: #fcd34d;
}

.dev-app__scroll-test-notice strong {
  font-size: 18px;
  display: block;
  margin-bottom: 12px;
}

.dev-app__scroll-test-notice p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.5;
  color: #fde68a;
}

/* Mobile responsive styles */
@media screen and (max-width: 768px) {
  .dev-app {
    --header-height: auto;
    overflow-x: hidden;
  }

  .dev-app__layout {
    overflow-x: hidden;
  }

  .dev-app__header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding: 16px;
  }

  .dev-app__brand {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .dev-app__logo {
    width: 48px;
    height: 48px;
  }

  .dev-app__title {
    font-size: 18px;
  }

  .dev-app__meta-row {
    flex-wrap: wrap;
    gap: 6px;
  }

  .dev-app__header-actions {
    align-items: stretch;
    width: 100%;
  }

  .dev-app__header-buttons {
    flex-direction: column;
    gap: 8px;
  }

  .dev-app__header-export-btn {
    width: 100%;
    text-align: center;
  }

  .dev-app__upload-control {
    flex-direction: column;
    align-items: stretch;
  }

  .dev-app__url-form {
    flex-direction: column;
  }

  .dev-app__url-input {
    width: 100%;
  }

  .dev-app__main {
    overflow-x: hidden;
  }

  .dev-app__view {
    padding-top: 10px;
    overflow-x: hidden;
  }
}
</style>
