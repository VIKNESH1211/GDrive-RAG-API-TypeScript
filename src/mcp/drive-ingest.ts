import { google } from 'googleapis';
import dotenv from 'dotenv';
import pdf from 'pdf-parse/lib/pdf-parse.js';

dotenv.config();

export async function ingestFromDrive(folderId: string) {
  const credentialsJson = process.env.GOOGLE_APPLICATION_CREDENTIALS;

  if (!credentialsJson) {
    throw new Error("GOOGLE_APPLICATION_CREDENTIALS is not set");
  }

  const credentials = JSON.parse(credentialsJson);

  const auth = new google.auth.JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: ['https://www.googleapis.com/auth/drive.readonly'],
  });

  const drive = google.drive({ version: 'v3', auth });

  try {
    // 1. List files within the specified folder
    const res = await drive.files.list({
      q: `'${folderId}' in parents and trashed = false and mimeType = 'application/pdf'`,
      fields: 'files(id, name, mimeType)',
      pageSize: 50,
    });

    const files = res.data.files;
    if (!files || files.length === 0) {
      console.log('❌ No PDF files found in the folder.');
      return [];
    }

    console.log('📂 PDFs in folder:');
    for (const file of files) {
      console.log(`- ${file.name} (${file.id})`);
    }

    // 2. Process each file (stream and extract text)
    const documents = [];
    for (const file of files) {
      const fileStream = await drive.files.get(
        { fileId: file.id, alt: 'media' },
        { responseType: 'stream' }
      );

      const chunks: Uint8Array[] = [];
      await new Promise((resolve, reject) => {
        fileStream.data
          .on('data', (chunk) => chunks.push(chunk))
          .on('end', resolve)
          .on('error', reject);
      });

      const buffer = Buffer.concat(chunks);
      const pdfData = await pdf(buffer);

      documents.push({
        name: file.name,
        id: file.id,
        text: pdfData.text,
      });

      console.log(`✅ Extracted from ${file.name}`);
    }

    return documents;

  } catch (error: any) {
    console.error('🚫 Error fetching files from Drive:', error.message || error);
    return [];
  }
}
