<script lang="ts">
	/**
	 * RAG Toggle - Enable/disable knowledge search
	 * Author: Kanwarraj Singh
	 */
	import { ragStore, ragIsAvailable, ragIsEnabled, ragDocuments } from '$lib/stores/rag.svelte';
	import { Database } from '@lucide/svelte';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import Button from '$lib/components/ui/button/button.svelte';

	let { onclick } = $props<{ onclick?: () => void }>();

	const isAvailable = $derived(ragIsAvailable());
	const isEnabled = $derived(ragIsEnabled());
	const documents = $derived(ragDocuments());
	const docCount = $derived(documents.length);

	function handleToggle(e: MouseEvent) {
		e.stopPropagation();
		ragStore.toggleEnabled();
	}
</script>

<Tooltip.Root>
	<Tooltip.Trigger>
		<Button
			variant={isEnabled && isAvailable ? 'default' : 'outline'}
			size="sm"
			class="gap-1.5 {!isAvailable ? 'opacity-50' : ''}"
			disabled={!isAvailable}
			onclick={onclick || handleToggle}
		>
			<Database class="h-4 w-4" />
			<span class="hidden sm:inline">
				{isAvailable ? `KB (${docCount})` : 'KB Offline'}
			</span>
		</Button>
	</Tooltip.Trigger>
	<Tooltip.Content>
		{#if !isAvailable}
			RAG service is offline
		{:else if isEnabled}
			Knowledge search enabled ({docCount} documents)
		{:else}
			Knowledge search disabled
		{/if}
	</Tooltip.Content>
</Tooltip.Root>
