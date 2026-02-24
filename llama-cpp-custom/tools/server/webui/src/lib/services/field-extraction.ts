import { getJsonHeaders } from '$lib/utils';

export interface FieldExtractionFile {
	name: string;
	base64Images: string[];
}

export interface FieldExtractionResult {
	filename: string;
	success: boolean;
	tableMarkdown: string;
	ocrContent: string;
	fieldsExtracted: string[];
	error?: string;
	processingTime: number;
}

export interface ExtractionProgress {
	stage: 'ocr' | 'extraction';
	fileIndex: number;
	totalFiles: number;
	filename: string;
	pageIndex?: number;
	totalPages?: number;
}

export interface ExtractionModelConfig {
	visionModel: string | null;
	thinkingModel: string | null;
}

function buildOCRPrompt(): string {
	return `You are a document OCR engine. Extract ALL text content from this document image exactly as it appears. Preserve the document structure including headings, paragraphs, tables, lists, and key-value pairs. Output the content in clean markdown format. Do not add any commentary or explanation - output ONLY the extracted text content.`;
}

function buildFieldExtractionPrompt(fields: string[], markdownContent: string): string {
	const fieldsStr = fields.map((f) => `"${f}"`).join(', ');

	return `You are a data extraction assistant. Your task is to extract specific fields from the provided document text and return them as a markdown table.

## Fields to Extract
${fieldsStr}

## Instructions
1. Carefully read through the document content provided below.
2. Extract the values for each of the requested fields.
3. If a field appears multiple times (e.g., in multiple rows of data), include all occurrences.
4. If a field value is not found, use "N/A" as the value.
5. Return ONLY a markdown table with the extracted data.
6. The table should have headers matching the field names.
7. Each row should represent a logical record/entry from the document.
8. If the document contains tabular data, preserve the row structure.
9. Do NOT include any explanation or text outside the markdown table.

## Document Content
\`\`\`
${markdownContent}
\`\`\`

## Output Format
Return a markdown table like this:
| Field1 | Field2 | Field3 |
|--------|--------|--------|
| value1 | value2 | value3 |

Now extract the fields and return the markdown table:`;
}

function extractTableFromResponse(responseText: string): string {
	let cleaned = responseText.trim();

	if (cleaned.startsWith('```')) {
		const lines = cleaned.split('\n');
		if (lines[0].startsWith('```')) {
			lines.shift();
		}
		if (lines.length > 0 && lines[lines.length - 1].trim() === '```') {
			lines.pop();
		}
		cleaned = lines.join('\n');
	}

	const lines = cleaned.split('\n');
	const tableLines: string[] = [];
	let inTable = false;

	for (const line of lines) {
		const stripped = line.trim();
		if (stripped.startsWith('|')) {
			inTable = true;
			tableLines.push(stripped);
		} else if (inTable && !stripped) {
			continue;
		} else if (inTable && !stripped.startsWith('|')) {
			if (stripped) {
				inTable = false;
			}
		}
	}

	if (tableLines.length > 0) {
		return tableLines.join('\n');
	}

	return cleaned.trim();
}

async function callChatCompletion(
	messages: Array<{ role: string; content: string | Array<Record<string, unknown>> }>,
	model?: string | null,
	signal?: AbortSignal
): Promise<string> {
	const body: Record<string, unknown> = {
		messages,
		stream: false,
		temperature: 0.1
	};

	if (model) {
		body.model = model;
	}

	const response = await fetch(`./v1/chat/completions`, {
		method: 'POST',
		headers: getJsonHeaders(),
		body: JSON.stringify(body),
		signal
	});

	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`API error (${response.status}): ${errorText}`);
	}

	const data = await response.json();
	const content = data.choices?.[0]?.message?.content;

	if (!content) {
		throw new Error('No content in API response');
	}

	return content;
}

export class FieldExtractionService {
	static async extractTextFromImages(
		base64Images: string[],
		modelName?: string | null,
		onProgress?: (pageIndex: number, totalPages: number) => void,
		signal?: AbortSignal
	): Promise<string> {
		const allText: string[] = [];
		const systemPrompt = buildOCRPrompt();

		for (let i = 0; i < base64Images.length; i++) {
			if (signal?.aborted) throw new Error('Aborted');

			onProgress?.(i, base64Images.length);

			const messages = [
				{ role: 'system', content: systemPrompt },
				{
					role: 'user',
					content: [
						{
							type: 'image_url',
							image_url: { url: base64Images[i] }
						},
						{
							type: 'text',
							text: `Extract all text from this document image (page ${i + 1} of ${base64Images.length}).`
						}
					]
				}
			];

			const pageText = await callChatCompletion(messages, modelName, signal);
			allText.push(`--- Page ${i + 1} ---\n${pageText}`);
		}

		return allText.join('\n\n');
	}

	static async extractFields(
		markdownContent: string,
		fields: string[],
		modelName?: string | null,
		signal?: AbortSignal
	): Promise<string> {
		const prompt = buildFieldExtractionPrompt(fields, markdownContent);

		const messages = [
			{
				role: 'user',
				content: prompt
			}
		];

		const response = await callChatCompletion(messages, modelName, signal);
		return extractTableFromResponse(response);
	}

	static async processFile(
		file: FieldExtractionFile,
		fields: string[],
		modelConfig?: ExtractionModelConfig,
		onProgress?: (progress: ExtractionProgress) => void,
		signal?: AbortSignal
	): Promise<FieldExtractionResult> {
		const startTime = performance.now();

		try {
			onProgress?.({
				stage: 'ocr',
				fileIndex: 0,
				totalFiles: 1,
				filename: file.name
			});

			const ocrContent = await FieldExtractionService.extractTextFromImages(
				file.base64Images,
				modelConfig?.visionModel,
				(pageIndex, totalPages) => {
					onProgress?.({
						stage: 'ocr',
						fileIndex: 0,
						totalFiles: 1,
						filename: file.name,
						pageIndex,
						totalPages
					});
				},
				signal
			);

			if (!ocrContent.trim()) {
				return {
					filename: file.name,
					success: false,
					tableMarkdown: '',
					ocrContent: '',
					fieldsExtracted: fields,
					error: 'No text could be extracted from the document',
					processingTime: (performance.now() - startTime) / 1000
				};
			}

			onProgress?.({
				stage: 'extraction',
				fileIndex: 0,
				totalFiles: 1,
				filename: file.name
			});

			const tableMarkdown = await FieldExtractionService.extractFields(
				ocrContent,
				fields,
				modelConfig?.thinkingModel,
				signal
			);

			return {
				filename: file.name,
				success: true,
				tableMarkdown,
				ocrContent,
				fieldsExtracted: fields,
				processingTime: (performance.now() - startTime) / 1000
			};
		} catch (error) {
			return {
				filename: file.name,
				success: false,
				tableMarkdown: '',
				ocrContent: '',
				fieldsExtracted: fields,
				error: error instanceof Error ? error.message : 'Unknown error',
				processingTime: (performance.now() - startTime) / 1000
			};
		}
	}

	static async processFiles(
		files: FieldExtractionFile[],
		fields: string[],
		modelConfig?: ExtractionModelConfig,
		onProgress?: (progress: ExtractionProgress) => void,
		signal?: AbortSignal
	): Promise<FieldExtractionResult[]> {
		const results: FieldExtractionResult[] = [];

		for (let i = 0; i < files.length; i++) {
			if (signal?.aborted) break;

			const result = await FieldExtractionService.processFile(
				files[i],
				fields,
				modelConfig,
				(progress) => {
					onProgress?.({
						...progress,
						fileIndex: i,
						totalFiles: files.length
					});
				},
				signal
			);

			results.push(result);
		}

		return results;
	}

	static parseMarkdownTable(
		markdown: string
	): { headers: string[]; rows: string[][] } | null {
		const lines = markdown
			.split('\n')
			.map((l) => l.trim())
			.filter((l) => l.startsWith('|'));

		if (lines.length < 2) return null;

		const parseLine = (line: string): string[] =>
			line
				.split('|')
				.slice(1, -1)
				.map((cell) => cell.trim());

		const headers = parseLine(lines[0]);

		const isSeparator = (line: string) =>
			parseLine(line).every((cell) => /^[-:]+$/.test(cell));

		const dataStart = isSeparator(lines[1]) ? 2 : 1;
		const rows = lines.slice(dataStart).map(parseLine);

		return { headers, rows };
	}
}
