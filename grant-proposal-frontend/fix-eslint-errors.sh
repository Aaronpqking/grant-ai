#!/bin/bash

# Fix ESLint errors in the files mentioned in the error log

# Fix 'let' to 'const' issues in upload route files
sed -i '' 's/let \(key\|value\)/const \1/g' src/app/api/upload/route.ts
sed -i '' 's/let \(key\|value\)/const \1/g' src/app/api/upload-single/route.ts

# Fix unused imports in components
sed -i '' 's/import { .*CheckCircle, .*Users.* } from/import { } from/g' src/components/dashboard.tsx
sed -i '' 's/import DocumentUploadSection from/\/\/ import DocumentUploadSection from/g' src/components/full-proposal-builder.tsx
sed -i '' 's/import { QuickProposalRequest } from/\/\/ import { QuickProposalRequest } from/g' src/components/quick-proposal-form.tsx

# Fix unused variables
sed -i '' 's/const \(uploadProgress\|isUploading\|uploadStatus\) = /\/\/ const \1 = /g' src/components/*.tsx

# Fix 'let' to 'const' in api.ts
sed -i '' 's/let \(key\|value\)/const \1/g' src/lib/api.ts

echo "ESLint errors fixed! Please verify the changes before committing." 