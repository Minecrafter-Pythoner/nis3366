
try {
    python build_script.py --pre
    if ($?) {
        Write-Host "pre handle executed successfully." -ForegroundColor Green
    } else {
        Write-Host "pre handle failed." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "An error occurred while trying to pre handle: $_" -ForegroundColor Red
    exit 1
}

# 运行npm run build命令
try {
    cd ./frontend
    npm run build
    if ($?) {
        Write-Host "Build succeeded." -ForegroundColor Green
    } else {
        Write-Host "Build failed." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "An error occurred while trying to build the project: $_" -ForegroundColor Red
    exit 1
}


try {
    cd ../
    python build_script.py --end
    if ($?) {
        Write-Host "end_handle executed successfully." -ForegroundColor Green
    } else {
        Write-Host "end_handle failed." -ForegroundColor Red
    }
} catch {
    Write-Host "An error occurred while trying to execute end_handle: $_" -ForegroundColor Red
}
