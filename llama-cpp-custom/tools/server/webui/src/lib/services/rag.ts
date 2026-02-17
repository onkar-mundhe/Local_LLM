/**
 * RAG Service - API client for Knowledge Base operations
 * Author: Kanwarraj Singh
 * 
 * Handles communication with the RAG service for document management and search.
 */

// RAG Service URL - can be configured
const RAG_SERVICE_URL = 'http://127.0.0.1:8000';

export interface RAGDocument {
	id: number;
	filename: string;
	file_type: string | null;
	file_size: number | null;
	chunk_count: number;
	upload_date: string | null;
	status: string;
	collection_name: string;
	enabled: boolean;
}

export interface RAGSearchResult {
	content: string;
	source: string;
	page: number;
	chunk_index: number;
	score: number;
	metadata: Record<string, unknown>;
}

export interface RAGSearchResponse {
	query: string;
	results: RAGSearchResult[];
	total: number;
	context: string | null;
}

export interface RAGHealthResponse {
	status: string;
	service: string;
	llama_server_url: string;
	embedding_model: string;
	document_count: number;
	chunk_count: number;
}

export class RAGService {
	private static baseUrl = RAG_SERVICE_URL;

	/**
	 * Check if RAG service is available
	 */
	static async checkHealth(): Promise<RAGHealthResponse | null> {
		try {
			const response = await fetch(`${this.baseUrl}/health`, {
				method: 'GET',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) return null;
			return await response.json();
		} catch {
			return null;
		}
	}

	/**
	 * Get all documents in the knowledge base
	 */
	static async getDocuments(): Promise<RAGDocument[]> {
		try {
			const response = await fetch(`${this.baseUrl}/documents`, {
				method: 'GET',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) return [];
			const data = await response.json();
			return data.documents || [];
		} catch {
			return [];
		}
	}

	/**
	 * Upload a document to the knowledge base
	 */
	static async uploadDocument(file: File): Promise<{ success: boolean; id?: number; chunks?: number; error?: string }> {
		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch(`${this.baseUrl}/documents/upload`, {
				method: 'POST',
				body: formData
			});

			const data = await response.json();
			
			if (!response.ok) {
				return { success: false, error: data.detail || 'Upload failed' };
			}

			return { success: true, id: data.id, chunks: data.chunks };
		} catch (error) {
			return { success: false, error: error instanceof Error ? error.message : 'Upload failed' };
		}
	}

	/**
	 * Delete a document from the knowledge base
	 */
	static async deleteDocument(id: number): Promise<boolean> {
		try {
			const response = await fetch(`${this.baseUrl}/documents/${id}`, {
				method: 'DELETE'
			});
			return response.ok;
		} catch {
			return false;
		}
	}

	/**
	 * Toggle document enabled state for RAG queries
	 */
	static async toggleDocument(id: number, enabled: boolean): Promise<boolean> {
		try {
			const response = await fetch(`${this.baseUrl}/documents/${id}/toggle`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ enabled })
			});
			return response.ok;
		} catch {
			return false;
		}
	}

	/**
	 * Search the knowledge base
	 */
	static async search(query: string, k: number = 5): Promise<RAGSearchResponse | null> {
		try {
			const response = await fetch(`${this.baseUrl}/search`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query, k })
			});
			if (!response.ok) return null;
			return await response.json();
		} catch {
			return null;
		}
	}

	/**
	 * Get context for a query (formatted for LLM)
	 */
	static async getContext(query: string, k: number = 5): Promise<string | null> {
		const result = await this.search(query, k);
		return result?.context || null;
	}
}
