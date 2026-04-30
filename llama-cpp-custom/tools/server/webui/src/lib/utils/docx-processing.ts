/**
 * DOCX text extraction using mammoth (browser-safe).
 */

import mammoth from 'mammoth';
import { FileExtensionDocx, MimeTypeApplication } from '$lib/enums';

export function isDocxFile(file: File): boolean {
	const name = file.name.toLowerCase();
	if (name.endsWith(FileExtensionDocx.DOCX)) {
		return true;
	}
	const t = file.type;
	return t === MimeTypeApplication.DOCX || t === MimeTypeApplication.DOCM;
}

/**
 * Extract plain text from a Word .docx (Office Open XML) file.
 */
export async function convertDocxToText(file: File): Promise<string> {
	const arrayBuffer = await file.arrayBuffer();
	const result = await mammoth.extractRawText({ arrayBuffer });
	if (result.messages?.length) {
		for (const m of result.messages) {
			console.debug('[mammoth]', m.type, m.message);
		}
	}
	return result.value ?? '';
}
