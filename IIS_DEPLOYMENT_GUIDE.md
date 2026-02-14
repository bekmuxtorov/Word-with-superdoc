# Windows Server + IIS Deploy Qo'llanmasi

Bu qo'llanma SuperDoc loyihasini Windows Server'da IIS (Internet Information Services) orqali deploy qilish bo'yicha to'liq yo'riqnoma.

---

## 📋 Talab Qilinadigan Dasturlar

### 1. Windows Server
- **OS**: Windows Server 2016 yoki undan yuqori
- **IIS**: Version 10.0+

### 2. Node.js va npm
- **Node.js**: v16.0+ (tavsiya: v18 LTS)
- **npm**: v8.0+ yoki **pnpm** (tavsiya)

**Node.js o'rnatish:**
1. [nodejs.org](https://nodejs.org/) dan Windows installer yuklab oling
2. Installer'ni ishga tushiring va default sozlamalarni qabul qiling
3. Terminalda tekshiring:
```bash
node --version
npm --version
```

### 3. IIS va Kerakli Komponentlar

**IIS ni yoqish:**
1. `Server Manager` ni oching
2. `Manage` → `Add Roles and Features`
3. `Server Roles` → `Web Server (IIS)` ni belgilang
4. Quyidagi komponentlarni qo'shing:
   - ✅ Static Content
   - ✅ Default Document
   - ✅ HTTP Errors
   - ✅ HTTP Redirection
   - ✅ WebSocket Protocol (agar kerak bo'lsa)
5. `Install` tugmasini bosing

### 4. URL Rewrite Module (Majburiy!)

**Nima uchun kerak:** Vue/React SPA'lar uchun client-side routing ishlashi uchun.

**O'rnatish:**
1. [IIS URL Rewrite Module](https://www.iis.net/downloads/microsoft/url-rewrite) yuklab oling
2. Installer'ni ishga tushiring
3. IIS Manager'ni restart qiling

---

## 🔨 Loyihani Build Qilish

### 1. Loyihani Clone/Copy Qilish

Server'da loyihangizni olish:

```bash
# Git orqali (agar Git o'rnatilgan bo'lsa)
cd C:\inetpub\wwwroot
git clone https://github.com/your-repo/superdoc.git

# YOKI: Lokal mashinadan copy qiling
# Zip archive qilib, server'ga ko'chiring va extract qiling
```

### 2. Dependencies O'rnatish

```bash
cd C:\inetpub\wwwroot\superdoc

# pnpm bilan (tavsiya)
pnpm install

# YOKI npm bilan
npm install
```

> **⚠️ Diqqat:** `node_modules` juda katta bo'lishi mumkin (200MB+), shuning uchun timezone va internet tezligiga qarab 5-15 daqiqa vaqt ketishi mumkin.

### 3. Production Build

```bash
# Build jarayoni
pnpm run build

# YOKI
npm run build
```

**Build jarayoni nimalar qiladi:**
- ✅ TypeScript/Vue/React kodlarni kompilatsiya qiladi
- ✅ Fayllarni minify va optimize qiladi
- ✅ `dist` papkasiga production-ready fayllar yaratadi
- ✅ CSS va JavaScript bundle'larni yaratadi

**Build natijasi:**
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── ...
└── ...
```

---

## 🌐 IIS Konfiguratsiyasi

### 1. Yangi Website Yaratish

#### IIS Manager orqali:

1. `IIS Manager` ni oching (`inetmgr`)
2. Chap panelda server nomiga right-click → `Add Website`
3. Quyidagicha to'ldiring:

| Field | Qiymat |
|-------|--------|
| **Site name** | `SuperDoc` |
| **Physical path** | `C:\inetpub\wwwroot\superdoc\dist` |
| **Binding Type** | `http` |
| **IP address** | `All Unassigned` |
| **Port** | `9094` (yoki sizning port) |
| **Host name** | Bo'sh yoki domen nomi |

4. `OK` tugmasini bosing

#### PowerShell orqali (Professional):

```powershell
# Administrator PowerShell da ishga tushiring
Import-Module WebAdministration

New-WebSite -Name "SuperDoc" `
    -Port 9094 `
    -PhysicalPath "C:\inetpub\wwwroot\superdoc\dist" `
    -ApplicationPool "DefaultAppPool"

Start-WebSite -Name "SuperDoc"
```

### 2. URL Rewrite Qoidalarini Sozlash

**Maqsad:** Barcha route'lar (masalan, `/about`, `/user/123`) `index.html` ga yo'naltirilishi kerak.

#### Avtomatik (web.config fayli bilan):

`dist` papkasida `web.config` yarating:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Handle History Mode and custom 404/500" stopProcessing="true">
                    <match url=".*" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="/" />
                </rule>
            </rules>
        </rewrite>
        
        <!-- CORS Headers (agar kerak bo'lsa) -->
        <httpProtocol>
            <customHeaders>
                <add name="Access-Control-Allow-Origin" value="*" />
                <add name="Access-Control-Allow-Methods" value="GET, POST, PUT, DELETE, OPTIONS" />
                <add name="Access-Control-Allow-Headers" value="Content-Type, Authorization" />
            </customHeaders>
        </httpProtocol>
        
        <!-- MIME Types -->
        <staticContent>
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <mimeMap fileExtension=".woff" mimeType="application/font-woff" />
            <mimeMap fileExtension=".woff2" mimeType="application/font-woff2" />
        </staticContent>
    </system.webServer>
</configuration>
```

#### Manual (IIS Manager orqali):

1. IIS Manager'da `SuperDoc` site'ni tanlang
2. `URL Rewrite` ni double-click qiling
3. `Add Rule(s)` → `Blank rule`
4. Quyidagicha to'ldiring:

**Name:** `SPA Fallback`

**Pattern:** `.*`

**Conditions:**
- `{REQUEST_FILENAME}` is not a file
- `{REQUEST_FILENAME}` is not a directory

**Action Type:** `Rewrite`

**Rewrite URL:** `/`

5. `Apply` va so'ng `OK`

### 3. Application Pool Sozlamalari

```powershell
# Application Pool nomini olish
$poolName = "DefaultAppPool"  # yoki "SuperDoc"

# .NET CLR Version: No Managed Code (chunki bu static SPA)
Set-ItemProperty IIS:\AppPools\$poolName -Name managedRuntimeVersion -Value ""

# Enable 32-bit Applications: False
Set-ItemProperty IIS:\AppPools\$poolName -Name enable32BitAppOnWin64 -Value $false

# Start Mode: OnDemand (yoki AlwaysRunning)
Set-ItemProperty IIS:\AppPools\$poolName -Name startMode -Value "OnDemand"
```

### 4. Firewall Qoidalarini Ochish

```powershell
# Administrator PowerShell
New-NetFirewallRule -DisplayName "SuperDoc HTTP" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 9094 `
    -Action Allow
```

---

## 🔒 HTTPS Sozlash (SSL Certificate)

### 1. Self-Signed Certificate (Test uchun)

```powershell
# Self-signed certificate yaratish
$cert = New-SelfSignedCertificate -DnsName "superdoc.local" `
    -CertStoreLocation "cert:\LocalMachine\My" `
    -FriendlyName "SuperDoc SSL"

# IIS ga binding qo'shish
New-WebBinding -Name "SuperDoc" `
    -Protocol "https" `
    -Port 443 `
    -SslFlags 0

# Certificate bind qilish
$binding = Get-WebBinding -Name "SuperDoc" -Protocol "https"
$binding.AddSslCertificate($cert.Thumbprint, "my")
```

### 2. Production SSL (Let's Encrypt / Company Certificate)

**Let's Encrypt bilan (Win-ACME):**

1. [Win-ACME](https://www.win-acme.com/) yuklab oling
2. Administrator CMD/PowerShell da ishga tushiring
3. Yo'riqnomani kuzatib SSL certificate oling

**Company Certificate:**
1. IIS Manager → Server nom → `Server Certificates`
2. `Complete Certificate Request` yoki `Import`
3. Certificate faylini tanlang (.pfx)
4. Site'ga binding qo'shing: `Bindings` → `Add` → HTTPS

---

## ✅ Test va Verification

### 1. Lokal Testlar

```bash
# Browser orqali
http://localhost:9094
https://localhost

# PowerShell orqali
Invoke-WebRequest -Uri "http://localhost:9094" -UseBasicParsing
```

### 2. Network Testlar

Boshqa kompyuterdan:
```
http://SERVER_IP:9094
```

### 3. Routing Test

Quyidagi URL'lar ishlashi kerak:
- `http://SERVER_IP:9094/`
- `http://SERVER_IP:9094/about`
- `http://SERVER_IP:9094/user/123`

Agar 404 xatolik chiqsa → **URL Rewrite** to'g'ri o'rnatilmagan!

---

## 🐛 Troubleshooting

### Muammo 1: "HTTP Error 404.0 - Not Found"

**Sabab:** Physical path noto'g'ri yoki `dist` papka yo'q.

**Yechim:**
1. `dist` papka mavjudligini tekshiring
2. IIS Manager'da physical path to'g'riligini tekshiring
3. `dir C:\inetpub\wwwroot\superdoc\dist` buyrug'ini ishga tushiring

### Muammo 2: "403 Forbidden"

**Sabab:** IIS fayllarni o'qiy olmayapti (permissions issue).

**Yechim:**
```powershell
# IIS_IUSRS ga read permission berish
icacls "C:\inetpub\wwwroot\superdoc\dist" /grant "IIS_IUSRS:(OI)(CI)R" /T
```

### Muammo 3: SPA Routing ishlamayapti (404 on refresh)

**Sabab:** URL Rewrite o'rnatilmagan yoki to'g'ri konfiguratsiya qilinmagan.

**Yechim:**
1. URL Rewrite Module o'rnatilganligini tekshiring
2. `web.config` faylini yarating (yuqoridagi namuna)
3. IIS Manager'da URL Rewrite qoidalarini tekshiring

### Muammo 4: "Cannot GET /assets/..."

**Sabab:** Static fayllar to'g'ri serve qilinmayapti.

**Yechim:**
1. IIS'da `Static Content` handler yoqilganligini tekshiring
2. `web.config` da static content settings to'g'riligini tekshiring

### Muammo 5: Port allaqachon ishlatilmoqda

**Sabab:** 9094 port boshqa process tomonidan ishlatilmoqda.

**Yechim:**
```powershell
# Portni ishlatayotgan processni topish
netstat -ano | findstr :9094

# Process'ni to'xtatish (PID ni yuqoridagi natijadan oling)
taskkill /PID <PID> /F

# YOKI boshqa port ishlating
```

---

## 📊 Performance Optimization

### 1. Compression (Gzip/Brotli)

IIS Manager → `SuperDoc` site → `Compression`:
- ✅ Enable dynamic content compression
- ✅ Enable static content compression

**PowerShell orqali:**
```powershell
Set-WebConfigurationProperty -Filter "/system.webServer/httpCompression" `
    -PSPath "IIS:\Sites\SuperDoc" `
    -Name "directory" `
    -Value "%SystemDrive%\inetpub\temp\IIS Temporary Compressed Files"

Set-WebConfigurationProperty -Filter "/system.webServer/urlCompression" `
    -PSPath "IIS:\Sites\SuperDoc" `
    -Name "doStaticCompression" `
    -Value $true
```

### 2. Caching

`web.config` ga qo'shing:

```xml
<system.webServer>
    <staticContent>
        <clientCache cacheControlMode="UseMaxAge" cacheControlMaxAge="7.00:00:00" />
    </staticContent>
</system.webServer>
```

### 3. Minification

Build vaqtida avtomatik minify:
```json
// vite.config.js yoki webpack.config.js
{
  build: {
    minify: 'terser',
    terserOptions: {
      compress: { drop_console: true }
    }
  }
}
```

---

## 🔄 Auto-Deploy Script (Bonus)

`deploy.ps1` yarating:

```powershell
# ===============================
# SuperDoc Auto-Deploy Script
# ===============================

param(
    [string]$SiteName = "SuperDoc",
    [string]$Port = "9094",
    [string]$SourcePath = "C:\inetpub\wwwroot\superdoc"
)

Write-Host "🚀 SuperDoc Deploy Boshlandi..." -ForegroundColor Cyan

# 1. Git pull (agar git mavjud bo'lsa)
if (Test-Path "$SourcePath\.git") {
    Write-Host "📥 Git pull..." -ForegroundColor Yellow
    Set-Location $SourcePath
    git pull origin main
}

# 2. Dependencies
Write-Host "📦 Dependencies o'rnatish..." -ForegroundColor Yellow
pnpm install

# 3. Build
Write-Host "🔨 Build jarayoni..." -ForegroundColor Yellow
pnpm run build

# 4. IIS Restart
Write-Host "🔄 IIS Restart..." -ForegroundColor Yellow
Stop-WebSite -Name $SiteName
Start-Sleep -Seconds 2
Start-WebSite -Name $SiteName

# 5. Verification
Write-Host "✅ Tekshirish..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Deploy muvaffaqiyatli!" -ForegroundColor Green
} else {
    Write-Host "❌ Xatolik: Status $($response.StatusCode)" -ForegroundColor Red
}

Write-Host "🎉 Tayyor!" -ForegroundColor Cyan
```

**Ishlatish:**
```powershell
.\deploy.ps1
```

---

## 📝 Xulosa

Deploy jarayoni qisqacha:

1. ✅ Node.js va IIS o'rnatish
2. ✅ Loyihani clone/copy qilish
3. ✅ `pnpm install` → `pnpm run build`
4. ✅ IIS'da yangi site yaratish (`dist` papkaga)
5. ✅ URL Rewrite sozlash (`web.config`)
6. ✅ Firewall ochish
7. ✅ Test qilish

**Qo'shimcha Resurslar:**
- [IIS Documentation](https://docs.microsoft.com/en-us/iis/)
- [Vue.js Deployment Guide](https://router.vuejs.org/guide/essentials/history-mode.html#iis)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)

---

**Deploy qilishda omad! 🚀**
