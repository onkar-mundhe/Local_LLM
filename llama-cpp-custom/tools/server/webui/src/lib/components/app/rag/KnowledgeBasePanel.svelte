<script lang="ts">
	/**
	 * Knowledge Base Panel - Document management sidebar
	 * Author: Kanwarraj Singh
	 */
	import { ragStore, ragDocuments, ragIsAvailable, ragHealth, ragIsSelectionLimitReached, MAX_SELECTED_DOCS } from '$lib/stores/rag.svelte';
	import { FileText, Trash2, Upload, Database, RefreshCw, X, Check } from '@lucide/svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import { toast } from 'svelte-sonner';

	let { onClose } = $props<{ onClose?: () => void }>();
	
	let fileInput: HTMLInputElement;
	let isUploading = $state(false);

	const documents = $derived(ragDocuments());
	const isAvailable = $derived(ragIsAvailable());
	const health = $derived(ragHealth());
	const enabledCount = $derived(documents.filter(d => d.enabled).length);
	const selectionLimitReached = $derived(ragIsSelectionLimitReached());

	function formatFileSize(bytes: number | null): string {
		if (!bytes) return 'N/A';
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleDateString();
	}

	async function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		isUploading = true;
		try {
			const result = await ragStore.uploadDocument(file);
			if (result.success && result.autoDisabled) {
				toast.success(`Uploaded "${file.name}" (${result.chunks} chunks) - not selected (limit ${MAX_SELECTED_DOCS})`);
			} else if (result.success) {
				toast.success(`Uploaded "${file.name}" (${result.chunks} chunks)`);
			} else {
				toast.error(result.error || 'Upload failed');
			}
		} finally {
			isUploading = false;
			input.value = '';
		}
	}

	async function handleDelete(id: number, filename: string) {
		const success = await ragStore.deleteDocument(id);
		if (success) {
			toast.success(`Deleted "${filename}"`);
		} else {
			toast.error('Delete failed');
		}
	}

	async function handleToggleEnabled(id: number, currentEnabled: boolean, filename: string) {
		const newEnabled = !currentEnabled;
		const result = await ragStore.toggleDocumentEnabled(id, newEnabled);
		if (result.limitReached) {
			toast.error(`Selection limit reached (max ${MAX_SELECTED_DOCS}). Deselect a document first.`);
		} else if (result.success) {
			toast.success(`"${filename}" ${newEnabled ? 'enabled' : 'disabled'} for search`);
		} else {
			toast.error('Failed to update document');
		}
	}

	async function handleRefresh() {
		await ragStore.checkHealth();
		toast.success('Refreshed');
	}
</script>

<div class="flex h-full min-h-0 flex-col bg-background">
	<!-- Header -->
	<div class="flex flex-shrink-0 items-center justify-between border-b p-3 sm:p-4">
		<div class="flex min-w-0 items-center gap-2">
			<Database class="h-5 w-5 flex-shrink-0 text-primary" />
			<h2 class="truncate text-base font-semibold sm:text-lg">Knowledge Base</h2>
		</div>
		<div class="flex flex-shrink-0 items-center gap-1">
			<Tooltip.Root>
				<Tooltip.Trigger>
					<Button variant="ghost" size="icon" onclick={handleRefresh}>
						<RefreshCw class="h-4 w-4" />
					</Button>
				</Tooltip.Trigger>
				<Tooltip.Content>Refresh</Tooltip.Content>
			</Tooltip.Root>
			{#if onClose}
				<Button variant="ghost" size="icon" onclick={onClose}>
					<X class="h-4 w-4" />
				</Button>
			{/if}
		</div>
	</div>

	<!-- Status -->
	<div class="flex-shrink-0 border-b px-3 py-2 sm:px-4">
		{#if isAvailable}
			<div class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-green-600 sm:text-sm dark:text-green-400">
				<span class="flex items-center gap-2">
					<span class="h-2 w-2 flex-shrink-0 rounded-full bg-green-500"></span>
					<span>Connected</span>
				</span>
				<span class="text-muted-foreground">
					({enabledCount}/{documents.length} docs active, {health?.chunk_count || 0} chunks)
				</span>
			</div>
			{#if selectionLimitReached}
				<p class="mt-1 text-xs text-amber-600 dark:text-amber-400">
					Selection limit reached (max {MAX_SELECTED_DOCS})
				</p>
			{:else if documents.length > 0}
				<p class="mt-1 text-xs text-muted-foreground">
					Select up to {MAX_SELECTED_DOCS} docs ({MAX_SELECTED_DOCS - enabledCount} remaining)
				</p>
			{/if}
		{:else}
			<div class="flex items-center gap-2 text-xs text-red-600 sm:text-sm dark:text-red-400">
				<span class="h-2 w-2 rounded-full bg-red-500"></span>
				<span>RAG Service Offline</span>
			</div>
		{/if}
	</div>

	<!-- Upload Button -->
	<div class="flex-shrink-0 border-b p-3 sm:p-4">
		<input
			bind:this={fileInput}
			type="file"
			accept=".pdf,.docx,.txt,.md"
			class="hidden"
			onchange={handleFileSelect}
		/>
		<Button
			variant="outline"
			class="w-full"
			disabled={!isAvailable || isUploading}
			onclick={() => fileInput?.click()}
		>
			<Upload class="mr-2 h-4 w-4 flex-shrink-0" />
			<span class="truncate">{isUploading ? 'Uploading...' : 'Upload Document'}</span>
		</Button>
		<p class="mt-2 text-center text-xs text-muted-foreground">
			Supports PDF, DOCX, TXT, MD
		</p>
	</div>

	<!-- Documents List -->
	<div class="min-h-0 flex-1 overflow-y-auto p-3 sm:p-4">
		{#if documents.length === 0}
			<div class="flex flex-col items-center justify-center py-6 text-center sm:py-8">
				<FileText class="mb-3 h-10 w-10 text-muted-foreground/50 sm:mb-4 sm:h-12 sm:w-12" />
				<p class="text-sm text-muted-foreground">No documents uploaded yet</p>
				<p class="mt-1 px-2 text-xs text-muted-foreground">
					Upload documents to enable knowledge search
				</p>
			</div>
		{:else}
			<div class="space-y-2">
				{#each documents as doc (doc.id)}
					<div
						class="group flex items-start gap-2 rounded-lg border p-2.5 transition-all sm:gap-3 sm:p-3 {doc.enabled ? 'hover:bg-muted/50' : 'opacity-50 border-dashed hover:opacity-70'}"
					>
						<!-- Toggle Checkbox -->
						<Tooltip.Root>
							<Tooltip.Trigger>
								<button
									class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border-2 transition-colors {doc.enabled ? 'border-primary bg-primary text-primary-foreground' : (doc.enabled || !selectionLimitReached) ? 'border-muted-foreground/40 bg-transparent hover:border-muted-foreground' : 'border-muted-foreground/20 bg-muted/30 cursor-not-allowed'}"
									disabled={!doc.enabled && selectionLimitReached}
									onclick={() => handleToggleEnabled(doc.id, doc.enabled, doc.filename)}
								>
									{#if doc.enabled}
										<Check class="h-3 w-3" />
									{/if}
								</button>
							</Tooltip.Trigger>
							<Tooltip.Content>
								{#if !doc.enabled && selectionLimitReached}
									Selection limit reached (max {MAX_SELECTED_DOCS})
								{:else}
									{doc.enabled ? 'Click to exclude from search' : 'Click to include in search'}
								{/if}
							</Tooltip.Content>
						</Tooltip.Root>

						<FileText class="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
						<div class="min-w-0 flex-1 overflow-hidden">
							<p class="truncate text-sm font-medium {doc.enabled ? '' : 'line-through decoration-muted-foreground/40'}" title={doc.filename}>
								{doc.filename}
							</p>
							<p class="mt-0.5 line-clamp-2 text-xs text-muted-foreground sm:line-clamp-none">
								{doc.chunk_count} chunks · {formatFileSize(doc.file_size)} · {formatDate(doc.upload_date)}
								{#if !doc.enabled}
									· <span class="text-amber-500 dark:text-amber-400">excluded</span>
								{/if}
							</p>
						</div>
						<Tooltip.Root>
							<Tooltip.Trigger>
								<Button
									variant="ghost"
									size="icon"
									class="h-8 w-8 flex-shrink-0 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
									onclick={() => handleDelete(doc.id, doc.filename)}
								>
									<Trash2 class="h-4 w-4 text-destructive" />
								</Button>
							</Tooltip.Trigger>
							<Tooltip.Content>Delete document</Tooltip.Content>
						</Tooltip.Root>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

