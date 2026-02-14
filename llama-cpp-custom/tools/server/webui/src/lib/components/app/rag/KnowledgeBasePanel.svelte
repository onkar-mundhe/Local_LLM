<script lang="ts">
	/**
	 * Knowledge Base Panel - Document management sidebar
	 * Author: Kanwarraj Singh
	 */
	import { ragStore, ragDocuments, ragIsAvailable, ragHealth } from '$lib/stores/rag.svelte';
	import { FileText, Trash2, Upload, Database, RefreshCw, X } from '@lucide/svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import { toast } from 'svelte-sonner';

	let { onClose } = $props<{ onClose?: () => void }>();
	
	let fileInput: HTMLInputElement;
	let isUploading = $state(false);

	const documents = $derived(ragDocuments());
	const isAvailable = $derived(ragIsAvailable());
	const health = $derived(ragHealth());

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
			if (result.success) {
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

	async function handleRefresh() {
		await ragStore.checkHealth();
		toast.success('Refreshed');
	}
</script>

<div class="flex h-full flex-col bg-background">
	<!-- Header -->
	<div class="flex items-center justify-between border-b p-4">
		<div class="flex items-center gap-2">
			<Database class="h-5 w-5 text-primary" />
			<h2 class="text-lg font-semibold">Knowledge Base</h2>
		</div>
		<div class="flex items-center gap-1">
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
	<div class="border-b px-4 py-2">
		{#if isAvailable}
			<div class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
				<span class="h-2 w-2 rounded-full bg-green-500"></span>
				<span>Connected</span>
				<span class="text-muted-foreground">
					({health?.document_count || 0} docs, {health?.chunk_count || 0} chunks)
				</span>
			</div>
		{:else}
			<div class="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
				<span class="h-2 w-2 rounded-full bg-red-500"></span>
				<span>RAG Service Offline</span>
			</div>
		{/if}
	</div>

	<!-- Upload Button -->
	<div class="border-b p-4">
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
			<Upload class="mr-2 h-4 w-4" />
			{isUploading ? 'Uploading...' : 'Upload Document'}
		</Button>
		<p class="mt-2 text-center text-xs text-muted-foreground">
			Supports PDF, DOCX, TXT, MD
		</p>
	</div>

	<!-- Documents List -->
	<div class="flex-1 overflow-y-auto p-4">
		{#if documents.length === 0}
			<div class="flex flex-col items-center justify-center py-8 text-center">
				<FileText class="mb-4 h-12 w-12 text-muted-foreground/50" />
				<p class="text-sm text-muted-foreground">No documents uploaded yet</p>
				<p class="mt-1 text-xs text-muted-foreground">
					Upload documents to enable knowledge search
				</p>
			</div>
		{:else}
			<div class="space-y-2">
				{#each documents as doc (doc.id)}
					<div
						class="group flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50"
					>
						<FileText class="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
						<div class="min-w-0 flex-1">
							<p class="truncate text-sm font-medium" title={doc.filename}>
								{doc.filename}
							</p>
							<p class="text-xs text-muted-foreground">
								{doc.chunk_count} chunks · {formatFileSize(doc.file_size)} · {formatDate(doc.upload_date)}
							</p>
						</div>
						<Tooltip.Root>
							<Tooltip.Trigger>
								<Button
									variant="ghost"
									size="icon"
									class="h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
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
