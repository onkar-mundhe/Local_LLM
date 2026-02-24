<script lang="ts">
	import { X, Plus, FileUp, Download, Copy, Loader2, FileText } from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { toast } from 'svelte-sonner';
	import { fade, fly, slide } from 'svelte/transition';
	import { onMount } from 'svelte';
	import {
		FieldExtractionService,
		type FieldExtractionFile,
		type FieldExtractionResult,
		type ExtractionProgress,
		type ExtractionModelConfig
	} from '$lib/services/field-extraction';
	import { convertPDFToImage } from '$lib/utils/pdf-processing';
	import { modelsStore } from '$lib/stores/models.svelte';
	import { isRouterMode } from '$lib/stores/server.svelte';

	const MAX_FILES = 5;

	interface UploadedPDF {
		id: string;
		file: File;
		name: string;
		size: number;
		status: 'ready' | 'processing' | 'done' | 'error';
		base64Images?: string[];
	}

	let uploadedFiles = $state<UploadedPDF[]>([]);
	let fields = $state<string[]>([]);
	let fieldInput = $state('');
	let isExtracting = $state(false);
	let extractionResults = $state<FieldExtractionResult[]>([]);
	let progressInfo = $state<ExtractionProgress | null>(null);
	let abortController = $state<AbortController | null>(null);
	let fileInputRef = $state<HTMLInputElement | null>(null);
	let dragCounter = $state(0);
	let isDragOver = $state(false);

	let selectedVisionModel = $state<string | null>(null);
	let selectedThinkingModel = $state<string | null>(null);

	let isRouter = $derived(isRouterMode());
	let availableModels = $derived(modelsStore.models);

	function autoDetectModels() {
		const models = modelsStore.models;
		if (models.length === 0) return;

		if (!selectedVisionModel) {
			const vision = models.find(
				(m) => m.name.toLowerCase().includes('vision') || m.id.toLowerCase().includes('vision')
			);
			if (vision) selectedVisionModel = vision.model || vision.id;
		}

		if (!selectedThinkingModel) {
			const thinking = models.find(
				(m) => m.name.toLowerCase().includes('thinking') || m.id.toLowerCase().includes('thinking')
			);
			if (thinking) selectedThinkingModel = thinking.model || thinking.id;
		}

		if (!selectedVisionModel && models.length > 0) {
			selectedVisionModel = models[0].model || models[0].id;
		}
		if (!selectedThinkingModel && models.length > 0) {
			const fallback = models.length > 1 ? models[1] : models[0];
			selectedThinkingModel = fallback.model || fallback.id;
		}
	}

	function getModelConfig(): ExtractionModelConfig {
		return {
			visionModel: isRouter ? selectedVisionModel : null,
			thinkingModel: isRouter ? selectedThinkingModel : null
		};
	}

	onMount(async () => {
		if (modelsStore.models.length === 0) {
			await modelsStore.fetch();
		}
		autoDetectModels();
	});

	let parsedResults = $derived.by(() => {
		return extractionResults.map((result) => {
			const parsed = result.success
				? FieldExtractionService.parseMarkdownTable(result.tableMarkdown)
				: null;
			return { ...result, parsed };
		});
	});

	let consolidatedTable = $derived.by(() => {
		const allHeaders: string[] = ['Source File'];
		const allRows: string[][] = [];

		for (const result of parsedResults) {
			if (!result.parsed) continue;
			for (const h of result.parsed.headers) {
				if (!allHeaders.includes(h)) {
					allHeaders.push(h);
				}
			}
		}

		for (const result of parsedResults) {
			if (!result.parsed) continue;
			for (const row of result.parsed.rows) {
				const newRow: string[] = new Array(allHeaders.length).fill('');
				newRow[0] = result.filename;
				for (let i = 0; i < result.parsed.headers.length; i++) {
					const colIdx = allHeaders.indexOf(result.parsed.headers[i]);
					if (colIdx >= 0) {
						newRow[colIdx] = row[i] || '';
					}
				}
				allRows.push(newRow);
			}
		}

		if (allRows.length === 0) return null;
		return { headers: allHeaders, rows: allRows };
	});

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
	}

	async function handleFilesSelected(fileList: FileList | File[]) {
		const files = Array.from(fileList);
		const pdfFiles = files.filter((f) => f.type === 'application/pdf');

		if (pdfFiles.length === 0) {
			toast.error('Only PDF files are supported.');
			return;
		}

		const remaining = MAX_FILES - uploadedFiles.length;
		if (remaining <= 0) {
			toast.error(`Maximum ${MAX_FILES} files allowed.`);
			return;
		}

		const toAdd = pdfFiles.slice(0, remaining);
		if (pdfFiles.length > remaining) {
			toast.warning(`Only ${remaining} more file(s) can be added. Extra files were skipped.`);
		}

		for (const file of toAdd) {
			const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
			uploadedFiles = [
				...uploadedFiles,
				{
					id,
					file,
					name: file.name,
					size: file.size,
					status: 'ready'
				}
			];
		}
	}

	function handleFileInputChange(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			handleFilesSelected(input.files);
			input.value = '';
		}
	}

	function removeFile(id: string) {
		uploadedFiles = uploadedFiles.filter((f) => f.id !== id);
	}

	function clearAllFiles() {
		uploadedFiles = [];
		extractionResults = [];
	}

	function addFields() {
		const raw = fieldInput.trim();
		if (!raw) return;

		const newFields = raw
			.split(',')
			.map((f) => f.trim())
			.filter((f) => f.length > 0 && !fields.includes(f));

		if (newFields.length > 0) {
			fields = [...fields, ...newFields];
		}
		fieldInput = '';
	}

	function removeField(field: string) {
		fields = fields.filter((f) => f !== field);
	}

	function clearAllFields() {
		fields = [];
	}

	function handleFieldKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addFields();
		}
	}

	function handleDragEnter(event: DragEvent) {
		event.preventDefault();
		dragCounter++;
		if (event.dataTransfer?.types.includes('Files')) {
			isDragOver = true;
		}
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		dragCounter--;
		if (dragCounter === 0) {
			isDragOver = false;
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		isDragOver = false;
		dragCounter = 0;
		if (event.dataTransfer?.files) {
			handleFilesSelected(event.dataTransfer.files);
		}
	}

	async function startExtraction() {
		if (uploadedFiles.length === 0) {
			toast.error('Please upload at least one PDF file.');
			return;
		}
		if (fields.length === 0) {
			toast.error('Please add at least one field to extract.');
			return;
		}

		isExtracting = true;
		extractionResults = [];
		const controller = new AbortController();
		abortController = controller;

		try {
			const extractionFiles: FieldExtractionFile[] = [];

			for (let i = 0; i < uploadedFiles.length; i++) {
				if (controller.signal.aborted) break;

				const uf = uploadedFiles[i];
				uploadedFiles = uploadedFiles.map((f) =>
					f.id === uf.id ? { ...f, status: 'processing' as const } : f
				);

				progressInfo = {
					stage: 'ocr',
					fileIndex: i,
					totalFiles: uploadedFiles.length,
					filename: uf.name
				};

				let images = uf.base64Images;
				if (!images) {
					images = await convertPDFToImage(uf.file, 2.0);
					uploadedFiles = uploadedFiles.map((f) =>
						f.id === uf.id ? { ...f, base64Images: images } : f
					);
				}

				extractionFiles.push({
					name: uf.name,
					base64Images: images!
				});
			}

			const results = await FieldExtractionService.processFiles(
				extractionFiles,
				fields,
				getModelConfig(),
				(progress) => {
					progressInfo = progress;
				},
				controller.signal
			);

			extractionResults = results;

			uploadedFiles = uploadedFiles.map((f) => {
				const result = results.find((r) => r.filename === f.name);
				return {
					...f,
					status: result?.success ? ('done' as const) : ('error' as const)
				};
			});

			const successCount = results.filter((r) => r.success).length;
			if (successCount === results.length) {
				toast.success(`Extraction complete for ${successCount} file(s).`);
			} else {
				toast.warning(
					`Extraction done: ${successCount}/${results.length} succeeded.`
				);
			}
		} catch (error) {
			if (error instanceof Error && error.message !== 'Aborted') {
				toast.error(`Extraction failed: ${error.message}`);
			}
			uploadedFiles = uploadedFiles.map((f) =>
				f.status === 'processing' ? { ...f, status: 'error' as const } : f
			);
		} finally {
			isExtracting = false;
			progressInfo = null;
			abortController = null;
		}
	}

	function stopExtraction() {
		abortController?.abort();
		abortController = null;
	}

	function copyTable() {
		if (!consolidatedTable) return;

		const { headers, rows } = consolidatedTable;
		let text = headers.join('\t') + '\n';
		for (const row of rows) {
			text += row.join('\t') + '\n';
		}

		navigator.clipboard.writeText(text).then(() => {
			toast.success('Table copied to clipboard.');
		});
	}

	function exportToExcel() {
		if (!consolidatedTable) return;

		const { headers, rows } = consolidatedTable;
		let csv = headers.map((h) => `"${h.replace(/"/g, '""')}"`).join(',') + '\n';
		for (const row of rows) {
			csv += row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',') + '\n';
		}

		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `extraction_results_${Date.now()}.csv`;
		a.click();
		URL.revokeObjectURL(url);

		toast.success('CSV file downloaded.');
	}

	function getProgressText(): string {
		if (!progressInfo) return '';
		const { stage, fileIndex, totalFiles, filename, pageIndex, totalPages } = progressInfo;

		if (stage === 'ocr') {
			const pageStr =
				pageIndex !== undefined && totalPages
					? ` (page ${pageIndex + 1}/${totalPages})`
					: '';
			return `OCR: ${filename}${pageStr} [${fileIndex + 1}/${totalFiles}]`;
		}
		return `Extracting fields: ${filename} [${fileIndex + 1}/${totalFiles}]`;
	}
</script>

<div class="flex h-full flex-col overflow-hidden">
	<div class="flex items-center justify-between border-b px-6 py-3">
		<div>
			<h2 class="text-lg font-semibold">Custom Field Extraction</h2>
			<p class="text-sm text-muted-foreground">
				Extract specific fields from up to {MAX_FILES} PDFs. Same fields applied to all documents.
			</p>
		</div>
		<div class="flex items-center gap-2">
			<div class="flex items-center gap-1.5 text-sm">
				<span
					class="inline-block h-2 w-2 rounded-full {isExtracting
						? 'bg-amber-500 animate-pulse'
						: 'bg-green-500'}"
				></span>
				<span class="text-muted-foreground">{isExtracting ? 'Processing' : 'Ready'}</span>
			</div>
		</div>
	</div>

	{#if isRouter && availableModels.length > 1}
		<div class="flex flex-wrap items-center gap-4 border-b px-6 py-2.5 text-sm">
			<label class="flex items-center gap-2">
				<span class="text-muted-foreground whitespace-nowrap">OCR Model:</span>
				<select
					class="rounded-md border bg-background px-2 py-1 text-sm"
					bind:value={selectedVisionModel}
					disabled={isExtracting}
				>
					{#each availableModels as model (model.id)}
						<option value={model.model || model.id}>{model.name}</option>
					{/each}
				</select>
			</label>
			<label class="flex items-center gap-2">
				<span class="text-muted-foreground whitespace-nowrap">Extraction Model:</span>
				<select
					class="rounded-md border bg-background px-2 py-1 text-sm"
					bind:value={selectedThinkingModel}
					disabled={isExtracting}
				>
					{#each availableModels as model (model.id)}
						<option value={model.model || model.id}>{model.name}</option>
					{/each}
				</select>
			</label>
		</div>
	{/if}

	<div class="flex-1 overflow-y-auto px-6 py-4">
		{#if extractionResults.length > 0 && consolidatedTable}
			<div class="space-y-4" in:fade={{ duration: 200 }}>
				<div class="flex items-center justify-between">
					<h3 class="text-base font-semibold">
						Extraction Results ({extractionResults.filter((r) => r.success).length} files)
					</h3>
					<Button variant="default" size="sm" onclick={exportToExcel}>
						<Download class="mr-1.5 h-4 w-4" />
						Export All to Excel
					</Button>
				</div>

				<div class="space-y-2">
					{#each extractionResults as result}
						<a
							href={URL.createObjectURL(
								uploadedFiles.find((f) => f.name === result.filename)?.file ??
									new Blob()
							)}
							target="_blank"
							class="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs text-primary hover:bg-accent"
						>
							<FileText class="h-3 w-3" />
							{result.filename}
						</a>
					{/each}
				</div>

				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<h4 class="text-sm font-medium text-muted-foreground">
							Consolidated Extraction Results
						</h4>
						<button
							onclick={copyTable}
							class="flex items-center gap-1 text-xs text-primary hover:underline"
						>
							<Copy class="h-3 w-3" />
							Copy Table
						</button>
					</div>

					<div class="overflow-x-auto rounded-lg border">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b bg-muted/50">
									{#each consolidatedTable.headers as header}
										<th class="whitespace-nowrap px-4 py-2.5 text-left font-semibold">
											{header}
										</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each consolidatedTable.rows as row, i}
									<tr class="border-b last:border-b-0 hover:bg-muted/30">
										{#each row as cell}
											<td class="px-4 py-2.5 whitespace-nowrap">{cell || 'N/A'}</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		{:else}
			<div class="space-y-6">
				<!-- File Upload Section -->
				<div class="space-y-3">
					<div
						class="relative rounded-xl border-2 border-dashed p-8 text-center transition-colors {isDragOver
							? 'border-primary bg-primary/5'
							: 'border-muted-foreground/25 hover:border-primary/50'}"
						ondragenter={handleDragEnter}
						ondragleave={handleDragLeave}
						ondragover={handleDragOver}
						ondrop={handleDrop}
						role="region"
						aria-label="File upload drop zone"
					>
						<FileUp class="mx-auto mb-3 h-10 w-10 text-muted-foreground/50" />
						<p class="mb-2 text-sm text-muted-foreground">
							Drop PDFs here (max {MAX_FILES} files)
						</p>
						<Button
							variant="default"
							size="sm"
							onclick={() => fileInputRef?.click()}
							disabled={isExtracting}
						>
							Browse Files
						</Button>
						<input
							bind:this={fileInputRef}
							type="file"
							accept="application/pdf"
							multiple
							class="hidden"
							onchange={handleFileInputChange}
						/>
					</div>

					{#if uploadedFiles.length > 0}
						<div class="space-y-2" in:slide={{ duration: 150 }}>
							<div class="flex items-center justify-between">
								<span class="text-sm font-medium">
									Selected Files ({uploadedFiles.length}/{MAX_FILES})
								</span>
								<button
									onclick={clearAllFiles}
									class="text-xs text-muted-foreground hover:text-foreground"
									disabled={isExtracting}
								>
									Clear All
								</button>
							</div>
							{#each uploadedFiles as uf (uf.id)}
								<div
									class="flex items-center justify-between rounded-lg border px-3 py-2"
									in:fly={{ y: 10, duration: 150 }}
								>
									<div class="flex items-center gap-2 overflow-hidden">
										<FileText class="h-4 w-4 shrink-0 text-muted-foreground" />
										<div class="min-w-0">
											<p class="truncate text-sm font-medium">{uf.name}</p>
											<p class="text-xs text-muted-foreground">
												{formatFileSize(uf.size)}
												{#if uf.status === 'ready'}
													<span class="text-green-600"> - Ready</span>
												{:else if uf.status === 'processing'}
													<span class="text-amber-600"> - Processing...</span>
												{:else if uf.status === 'done'}
													<span class="text-green-600"> - Done</span>
												{:else if uf.status === 'error'}
													<span class="text-red-600"> - Error</span>
												{/if}
											</p>
										</div>
									</div>
									<button
										onclick={() => removeFile(uf.id)}
										class="shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
										disabled={isExtracting}
										aria-label="Remove file"
									>
										<X class="h-4 w-4" />
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Fields Section -->
				<div class="space-y-3">
					<h3 class="text-sm font-semibold">Fields to Extract (applied to all PDFs)</h3>
					<div class="flex gap-2">
						<Input
							bind:value={fieldInput}
							placeholder="Enter field name(s) comma-separated for multiple fields..."
							onkeydown={handleFieldKeydown}
							disabled={isExtracting}
							class="flex-1"
						/>
						<Button
							variant="default"
							size="default"
							onclick={addFields}
							disabled={isExtracting || !fieldInput.trim()}
						>
							<Plus class="mr-1 h-4 w-4" />
							Add
						</Button>
					</div>

					{#if fields.length > 0}
						<div class="flex flex-wrap items-center gap-2" in:slide={{ duration: 150 }}>
							<span class="text-sm text-muted-foreground">
								Selected Fields ({fields.length}):
							</span>
							<button
								onclick={clearAllFields}
								class="text-xs font-medium text-destructive hover:underline"
								disabled={isExtracting}
							>
								Clear All
							</button>
							{#each fields as field (field)}
								<span
									class="inline-flex items-center gap-1 rounded-full border bg-muted px-3 py-1 text-xs font-medium"
									in:fly={{ x: -10, duration: 150 }}
								>
									{field}
									<button
										onclick={() => removeField(field)}
										class="text-muted-foreground hover:text-destructive"
										disabled={isExtracting}
									>
										<X class="h-3 w-3" />
									</button>
								</span>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Progress Info -->
				{#if isExtracting && progressInfo}
					<div class="space-y-2 rounded-lg border bg-muted/30 p-4" in:slide={{ duration: 150 }}>
						<div class="flex items-center gap-2">
							<Loader2 class="h-4 w-4 animate-spin text-primary" />
							<span class="text-sm font-medium">{getProgressText()}</span>
						</div>
						<div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
							<div
								class="h-full rounded-full bg-primary transition-all duration-300"
								style="width: {((progressInfo.fileIndex + (progressInfo.stage === 'extraction' ? 0.5 : 0)) / progressInfo.totalFiles) * 100}%"
							></div>
						</div>
					</div>
				{/if}

				<!-- Action Button -->
				{#if uploadedFiles.length > 0 && fields.length > 0}
					<div in:slide={{ duration: 150 }}>
						{#if isExtracting}
							<Button
								variant="destructive"
								class="w-full"
								onclick={stopExtraction}
							>
								Stop Extraction
							</Button>
						{:else}
							<Button
								variant="default"
								class="w-full bg-primary text-primary-foreground hover:bg-primary/90"
								onclick={startExtraction}
							>
								Extract Fields from All Documents
							</Button>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
