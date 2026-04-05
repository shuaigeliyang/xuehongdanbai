# ========================================
# 血浆游离血红蛋白检测系统 - 前端一键启动脚本
# 作者: 哈雷酱大小姐 (￣▽￣)／
# ========================================

# 设置错误处理
$ErrorActionPreference = "Stop"

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# 显示Banner
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "血浆游离血红蛋白检测系统 - 前端启动" "Cyan"
Write-ColorOutput "作者: 哈雷酱大小姐 (￣▽￣)／" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# 定义项目路径
$ProjectPath = "E:\外包\基于机器学习的血浆游离血红蛋白检测系统的设计与实现\frontend"

# 检查目录是否存在
if (!(Test-Path $ProjectPath)) {
    Write-ColorOutput "❌ 错误: frontend目录不存在！" "Red"
    Write-ColorOutput "   路径: $ProjectPath" "Red"
    Write-Host ""
    Write-ColorOutput "请确认路径是否正确！" "Yellow"
    pause
    exit 1
}

# 进入项目目录
Write-ColorOutput "[1/6] 进入项目目录..." "Yellow"
Set-Location $ProjectPath
Write-ColorOutput "    ✓ 当前目录: $((Get-Location).Path)" "Green"
Write-Host ""

# 检查Node.js
Write-ColorOutput "[2/6] 检查Node.js环境..." "Yellow"
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "    ✓ Node.js版本: $nodeVersion" "Green"

        # 检查版本是否满足要求
        $version = $nodeVersion -replace 'v', ''
        $majorVersion = [int]($version.Split('.')[0])
        if ($majorVersion -lt 16) {
            Write-ColorOutput "    ⚠️  警告: Node.js版本过低，建议使用v16或更高版本！" "Yellow"
        }
    } else {
        throw "Node.js未安装"
    }
} catch {
    Write-ColorOutput "    ❌ 错误: Node.js未安装或无法运行！" "Red"
    Write-Host ""
    Write-ColorOutput "    请先安装Node.js: https://nodejs.org/" "Cyan"
    Write-ColorOutput "    推荐安装LTS版本（长期支持版本）" "Cyan"
    Write-Host ""
    pause
    exit 1
}
Write-Host ""

# 检查npm
Write-ColorOutput "[3/6] 检查npm环境..." "Yellow"
try {
    $npmVersion = npm --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "    ✓ npm版本: $npmVersion" "Green"
    } else {
        throw "npm未安装"
    }
} catch {
    Write-ColorOutput "    ❌ 错误: npm未安装或无法运行！" "Red"
    Write-Host ""
    Write-ColorOutput "    npm通常随Node.js一起安装，请重新安装Node.js" "Cyan"
    Write-Host ""
    pause
    exit 1
}
Write-Host ""

# 检查依赖包
Write-ColorOutput "[4/6] 检查依赖包..." "Yellow"
if (!(Test-Path "node_modules")) {
    Write-ColorOutput "    ⚠️  node_modules不存在，需要安装依赖" "Yellow"
    Write-Host ""
    Write-ColorOutput "    正在安装依赖包，请稍候..." "Cyan"
    Write-ColorOutput "    这可能需要几分钟时间..." "Cyan"
    Write-Host ""

    try {
        npm install

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorOutput "    ✓ 依赖包安装完成！" "Green"
        } else {
            throw "npm install失败"
        }
    } catch {
        Write-Host ""
        Write-ColorOutput "    ❌ 错误: 依赖包安装失败！" "Red"
        Write-Host ""
        Write-ColorOutput "    可能的原因：" "Yellow"
        Write-ColorOutput "    1. 网络连接问题" "White"
        Write-ColorOutput "    2. npm源访问缓慢" "White"
        Write-ColorOutput "    3. 权限问题" "White"
        Write-Host ""
        Write-ColorOutput "    建议尝试：" "Cyan"
        Write-ColorOutput "    npm config set registry https://registry.npmmirror.com" "White"
        Write-ColorOutput "    npm install" "White"
        Write-Host ""
        pause
        exit 1
    }
} else {
    Write-ColorOutput "    ✓ 依赖包已安装" "Green"
}
Write-Host ""

# 检查package.json
Write-ColorOutput "[5/6] 检查项目配置..." "Yellow"
if (!(Test-Path "package.json")) {
    Write-ColorOutput "    ❌ 错误: package.json文件不存在！" "Red"
    Write-Host ""
    Write-ColorOutput "    请确认这是正确的React项目目录！" "Yellow"
    Write-Host ""
    pause
    exit 1
} else {
    Write-ColorOutput "    ✓ package.json存在" "Green"
}
Write-Host ""

# 启动React开发服务器
Write-ColorOutput "[6/6] 启动React开发服务器..." "Yellow"
Write-Host ""
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
Write-ColorOutput "重要提示:" "Cyan"
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
Write-Host ""
Write-ColorOutput "1. 首次启动需要1-3分钟编译时间，请耐心等待！" "Yellow"
Write-ColorOutput "2. 编译成功后，浏览器会自动打开" "Yellow"
Write-ColorOutput "3. 如果浏览器没有自动打开，请手动访问:" "Yellow"
Write-ColorOutput "   http://localhost:3000" "White"
Write-Host ""
Write-ColorOutput "4. 确保后端服务已启动在8000端口！" "Yellow"
Write-Host ""
Write-ColorOutput "5. 按 Ctrl+C 可以停止服务器" "Gray"
Write-Host ""
Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
Write-Host ""
Write-ColorOutput "正在启动..." "Green"
Write-Host ""

# 设置环境变量（可选）
$env:BROWSER = "none"  # 禁用自动打开浏览器，如果需要自动打开请注释掉这行

# 启动npm
try {
    npm start
} catch {
    Write-Host ""
    Write-ColorOutput "❌ 启动失败！" "Red"
    Write-Host ""
    Write-ColorOutput "请查看上方的错误信息，可能的原因：" "Yellow"
    Write-ColorOutput "1. 端口3000被占用" "White"
    Write-ColorOutput "2. 依赖包损坏" "White"
    Write-ColorOutput "3. 代码语法错误" "White"
    Write-Host ""
    Write-ColorOutput "解决方案：" "Cyan"
    Write-ColorOutput "1. 检查并关闭占用3000端口的程序" "White"
    Write-ColorOutput "2. 运行: Remove-Item -Recurse -Force node_modules" "White"
    Write-ColorOutput "3. 运行: npm install" "White"
    Write-ColorOutput "4. 再次运行此脚本" "White"
    Write-Host ""
    pause
    exit 1
}
