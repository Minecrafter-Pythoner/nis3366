python build_script.py --pre
cd frontend && pnpm run build && cd ..
python build_script.py --end
mv frontend/dist.zip .
echo "Build complete"