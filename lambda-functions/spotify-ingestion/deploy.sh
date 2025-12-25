#!/bin/bash
# Package Lambda function with dependencies

echo "Creating deployment package..."

# Create clean directory
rm -rf package
mkdir package

# Install dependencies to package directory
pip install -r requirements.txt -t package/

# Copy source code
cp -r src/* package/

# Create zip file
cd package
zip -r ../spotify-ingestion-lambda.zip .
cd ..

echo "✅ Deployment package created: spotify-ingestion-lambda.zip"
ls -lh spotify-ingestion-lambda.zip
