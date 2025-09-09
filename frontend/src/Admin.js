import React, { useState, useEffect } from 'react';
import './Admin.css';

function Admin() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  // Load actual documents from ChromaDB via API
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8002/admin/documents');
      const data = await response.json();
      
      // Transform API response to match UI format
      const documents = data.documents.map(doc => ({
        id: doc.id,
        name: doc.filename,
        size: doc.file_size,
        type: doc.content_type,
        uploadDate: doc.upload_time,
        status: 'processed',
        chunks: doc.chunks || 1,
        preview: doc.preview,
        title: doc.title,
        category: doc.category,
        document_type: doc.document_type,
        topics: doc.topics || [],
        summary: doc.summary,
        actions: doc.actions || {}
      }));
      
      setUploadedFiles(documents);
    } catch (error) {
      console.error('Error loading documents:', error);
      setUploadedFiles([]);
    }
  };

  const handleFileSelect = (files) => {
    const fileArray = Array.from(files);
    setSelectedFiles(fileArray);
  };

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    
    // Upload each file to the backend
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      
      // Add file to UI with uploading status
      const tempFile = {
        id: `temp_${Date.now()}_${i}`,
        name: file.name,
        size: file.size,
        type: file.type,
        uploadDate: new Date().toISOString(),
        status: 'uploading',
        chunks: 0
      };
      setUploadedFiles(prev => [...prev, tempFile]);
      
      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload to backend
        const response = await fetch('http://localhost:8002/upload', {
          method: 'POST',
          body: formData,
        });
        
        if (response.ok) {
          const result = await response.json();
          // Update with successful upload
          setUploadedFiles(prev => 
            prev.map(doc => 
              doc.id === tempFile.id 
                ? {
                    ...doc,
                    id: result.document_id,
                    status: 'processed',
                    chunks: 1,
                    uploadDate: result.upload_time
                  }
                : doc
            )
          );
        } else {
          const error = await response.json();
          // Update with error status
          setUploadedFiles(prev => 
            prev.map(doc => 
              doc.id === tempFile.id 
                ? { ...doc, status: 'error', error: error.detail }
                : doc
            )
          );
        }
      } catch (error) {
        console.error('Upload error:', error);
        // Update with error status
        setUploadedFiles(prev => 
          prev.map(doc => 
            doc.id === tempFile.id 
              ? { ...doc, status: 'error', error: 'Network error' }
              : doc
          )
        );
      }
    }
    
    setSelectedFiles([]);
    setIsUploading(false);
    
    // Reload documents to get fresh data
    setTimeout(() => {
      loadDocuments();
    }, 1000);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    handleFileSelect(files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    if (type.includes('pdf')) {
      return (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10,9 9,9 8,9"/>
        </svg>
      );
    } else if (type.includes('word') || type.includes('document')) {
      return (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10,9 9,9 8,9"/>
        </svg>
      );
    } else if (type.includes('text')) {
      return (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <line x1="12" y1="9" x2="8" y2="9"/>
        </svg>
      );
    } else {
      return (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
        </svg>
      );
    }
  };

  const getFileIconClass = (type) => {
    if (type.includes('pdf')) return 'pdf';
    if (type.includes('word') || type.includes('document')) return 'doc';
    if (type.includes('text')) return 'txt';
    return 'unknown';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'processed':
        return <span className="status-badge processed">✓ Processed</span>;
      case 'processing':
        return <span className="status-badge processing">⟳ Processing</span>;
      case 'uploading':
        return <span className="status-badge uploading">↑ Uploading</span>;
      case 'error':
        return <span className="status-badge error">✗ Error</span>;
      default:
        return <span className="status-badge pending">○ Pending</span>;
    }
  };

  const removeFile = async (fileId) => {
    try {
      const response = await fetch(`http://localhost:8002/documents/${fileId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Remove from UI
        setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
      } else {
        const error = await response.json();
        console.error('Delete error:', error.detail);
        alert('Failed to delete document: ' + error.detail);
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete document: Network error');
    }
  };

  const downloadFile = async (fileId, filename) => {
    try {
      const response = await fetch(`http://localhost:8002/download/${fileId}`);
      
      if (response.ok) {
        // Create blob from response
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const error = await response.json();
        console.error('Download error:', error.detail);
        alert('Failed to download document: ' + error.detail);
      }
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download document: Network error');
    }
  };


  const processedCount = uploadedFiles.filter(file => file.status === 'processed').length;
  const totalChunks = uploadedFiles.reduce((acc, file) => acc + (file.chunks || 0), 0);

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div className="admin-title">
          <h1>Knowledge Base Administration</h1>
          <p>Upload and manage documents for the AI knowledge base</p>
        </div>
        <div className="admin-stats">
          <div className="stat-card">
            <div className="stat-number">{uploadedFiles.length}</div>
            <div className="stat-label">Total Documents</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{processedCount}</div>
            <div className="stat-label">Processed</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{totalChunks}</div>
            <div className="stat-label">Knowledge Chunks</div>
          </div>
        </div>
        <a href="/" className="back-to-chat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          Back to Chat
        </a>
      </div>

      <div className="admin-content">
        <div className="upload-section">
          <div 
            className={`upload-area ${dragOver ? 'drag-over' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div className="upload-content">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17,8 12,3 7,8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <h3>Upload Knowledge Documents</h3>
              <p>Drag and drop files here, or click to select</p>
              <p className="file-types">
                Supported: PDF, DOC, DOCX, TXT, RTF, HTML, MD, CSV, XLSX
              </p>
              <input 
                type="file" 
                multiple 
                accept=".pdf,.doc,.docx,.txt,.rtf,.html,.md,.csv,.xlsx"
                onChange={(e) => handleFileSelect(e.target.files)}
                className="file-input"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="upload-btn">
                Choose Files
              </label>
            </div>
          </div>

          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h4>Selected Files ({selectedFiles.length})</h4>
              <div className="selected-files-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="selected-file">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{formatFileSize(file.size)}</span>
                  </div>
                ))}
              </div>
              <button 
                className="upload-selected-btn" 
                onClick={handleFileUpload}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Upload Selected Files'}
              </button>
            </div>
          )}
        </div>

        <div className="documents-section">
          <div className="section-header">
            <h2>Knowledge Base Documents</h2>
            <div className="section-actions">
              <button className="refresh-btn" onClick={() => window.location.reload()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Refresh
              </button>
            </div>
          </div>
            
          <div className="documents-grid">
            {uploadedFiles.length === 0 ? (
              <div className="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10,9 9,9 8,9"/>
                </svg>
                <h3>No documents in knowledge base</h3>
                <p>Upload your first document to get started</p>
              </div>
            ) : (
              uploadedFiles.map(file => (
                <div key={file.id} className={`document-card ${file.status}`}>
                  {/* Header with Large Icon */}
                  <div className="document-header">
                    <div className={`document-icon ${getFileIconClass(file.type)}`}>
                      {getFileIcon(file.type)}
                    </div>
                    <h4 className="document-title" title={file.title || file.name}>
                      {file.title || file.name}
                    </h4>
                    <p className="document-subtitle">{file.name}</p>
                  </div>
                  
                  {/* Card Body */}
                  <div className="document-body">
                    {/* Status Badge */}
                    <div className="document-status">
                      {getStatusBadge(file.status)}
                    </div>
                    
                    {/* Document Info */}
                    <div className="document-info">
                      {/* Badges */}
                      <div className="document-badges">
                        <span className="category-badge">{file.category || 'Document'}</span>
                        {file.document_type && file.document_type !== 'Unknown' && (
                          <span className="doc-type-badge">{file.document_type}</span>
                        )}
                      </div>
                      
                      {/* Summary */}
                      {file.summary && (
                        <p className="document-summary">{file.summary}</p>
                      )}
                      
                      {/* Topics */}
                      {file.topics && file.topics.length > 0 && file.topics[0] && (
                        <div className="document-topics">
                          {file.topics.slice(0, 3).map((topic, idx) => (
                            <span key={idx} className="topic-tag">{topic.trim()}</span>
                          ))}
                        </div>
                      )}
                      
                      {/* Meta Information */}
                      <div className="document-meta">
                        <div className="document-meta-item">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                          </svg>
                          <span>{formatFileSize(file.size)}</span>
                        </div>
                        
                        <div className="document-meta-item">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                          </svg>
                          <span>
                            {new Date(file.uploadDate).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric'
                            })}
                          </span>
                        </div>
                        
                        {file.chunks > 0 && (
                          <div className="document-meta-item">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                              <polyline points="14,2 14,8 20,8"/>
                              <line x1="16" y1="13" x2="8" y2="13"/>
                              <line x1="16" y1="17" x2="8" y2="17"/>
                              <polyline points="10,9 9,9 8,9"/>
                            </svg>
                            <span>{file.chunks} chunks</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Card Actions */}
                  <div className="document-actions">
                    {file.actions?.can_download && (
                      <button 
                        className="action-btn download-btn" 
                        title="Download Document"
                        disabled={file.status === 'uploading'}
                        onClick={() => downloadFile(file.id, file.name)}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="7,10 12,15 17,10"/>
                          <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                      </button>
                    )}
                    <button 
                      className="action-btn delete-btn" 
                      onClick={() => removeFile(file.id)} 
                      title="Delete Document"
                      disabled={file.status === 'uploading' || file.status === 'processing'}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3,6 5,6 21,6"/>
                        <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"/>
                      </svg>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Admin;