# Script to push FikaTutor Internal Tool to GitHub
# Make sure Git is installed before running this script

Write-Host "Initializing Git repository..." -ForegroundColor Green
git init

Write-Host "Adding remote repository..." -ForegroundColor Green
git remote add origin https://github.com/dVerse-Technologies/FikaTutor_internal_tool.git

Write-Host "Adding all files..." -ForegroundColor Green
git add .

Write-Host "Creating initial commit..." -ForegroundColor Green
git commit -m "Initial commit: FikaTutor Internal Tool - Document to JSON converter"

Write-Host "Pushing to GitHub..." -ForegroundColor Green
git branch -M main
git push -u origin main

Write-Host "Done! Your project has been pushed to GitHub." -ForegroundColor Green

