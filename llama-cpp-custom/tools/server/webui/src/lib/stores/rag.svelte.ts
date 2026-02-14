/**
 * RAG Store - Knowledge Base state management
 * Author: Kanwarraj Singh
 * 
 * Manages RAG service state including documents, health status, and settings.
 */

import { browser } from '$app/environment';
import { RAGService, type RAGDocument, type RAGHealthResponse } from '$lib/services/rag';

const RAG_SETTINGS_KEY = 'rag-settings';

interface RAGSettings {
	enabled: boolean;
	topK: number;
}

class RAGStore {
	// State
	documents = $state<RAGDocument[]>([]);
	health = $state<RAGHealthResponse | null>(null);
	isLoading = $state(false);
	isAvailable = $state(false);
	settings = $state<RAGSettings>({ enabled: true, topK: 5 });

	constructor() {
		if (browser) {
			this.loadSettings();
			this.checkHealth();
		}
	}

	private loadSettings() {
		try {
			const saved = localStorage.getItem(RAG_SETTINGS_KEY);
			if (saved) {
				this.settings = { ...this.settings, ...JSON.parse(saved) };
			}
		} catch {
			// Use defaults
		}
	}

	private saveSettings() {
		if (browser) {
			localStorage.setItem(RAG_SETTINGS_KEY, JSON.stringify(this.settings));
		}
	}

	/**
	 * Check RAG service health
	 */
	async checkHealth() {
		const health = await RAGService.checkHealth();
		this.health = health;
		this.isAvailable = health !== null && health.status === 'healthy';
		
		if (this.isAvailable) {
			await this.fetchDocuments();
		}
	}

	/**
	 * Fetch all documents
	 */
	async fetchDocuments() {
		this.isLoading = true;
		try {
			this.documents = await RAGService.getDocuments();
		} finally {
			this.isLoading = false;
		}
	}

	/**
	 * Upload a document
	 */
	async uploadDocument(file: File): Promise<{ success: boolean; error?: string }> {
		this.isLoading = true;
		try {
			const result = await RAGService.uploadDocument(file);
			if (result.success) {
				await this.fetchDocuments();
			}
			return result;
		} finally {
			this.isLoading = false;
		}
	}

	/**
	 * Delete a document
	 */
	async deleteDocument(id: number): Promise<boolean> {
		const success = await RAGService.deleteDocument(id);
		if (success) {
			await this.fetchDocuments();
		}
		return success;
	}

	/**
	 * Toggle RAG enabled state
	 */
	toggleEnabled() {
		this.settings.enabled = !this.settings.enabled;
		this.saveSettings();
	}

	/**
	 * Set RAG enabled state
	 */
	setEnabled(enabled: boolean) {
		this.settings.enabled = enabled;
		this.saveSettings();
	}

	/**
	 * Set top K results
	 */
	setTopK(k: number) {
		this.settings.topK = k;
		this.saveSettings();
	}

	/**
	 * Get context for a query
	 */
	async getContext(query: string): Promise<string | null> {
		if (!this.isAvailable || !this.settings.enabled) {
			return null;
		}
		return RAGService.getContext(query, this.settings.topK);
	}
}

export const ragStore = new RAGStore();
export const ragDocuments = () => ragStore.documents;
export const ragIsAvailable = () => ragStore.isAvailable;
export const ragIsEnabled = () => ragStore.settings.enabled;
export const ragHealth = () => ragStore.health;
