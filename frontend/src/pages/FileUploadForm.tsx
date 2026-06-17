import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getFileUploadById, createFileUpload, updateFileUpload } from '../api/client';

interface FileUploadFormData {
  filename: string;
  originalName: string;
  fileSize: number;
  mimeType: string;
  uploadDate: string;
  status: string;
  chunkCount: number;
  sessionId: string;
}

const FileUploadForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = !!id;

  const [formData, setFormData] = useState<FileUploadFormData>({
    filename: '',
    originalName: '',
    fileSize: 0,
    mimeType: '',
    uploadDate: new Date().toISOString().split('T')[0],
    status: 'pending',
    chunkCount: 0,
    sessionId: '',
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isEditMode) {
      fetchFileUpload();
    }
  }, [id]);

  const fetchFileUpload = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFileUploadById(id!);
      setFormData({
        filename: data.filename,
        originalName: data.originalName,
        fileSize: data.fileSize,
        mimeType: data.mimeType,
        uploadDate: data.uploadDate.split('T')[0],
        status: data.status,
        chunkCount: data.chunkCount,
        sessionId: data.sessionId,
      });
    } catch (err) {
      setError('Failed to load file upload data.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.filename.trim()) errors.filename = 'Filename is required.';
    if (!formData.originalName.trim()) errors.originalName = 'Original name is required.';
    if (formData.fileSize < 0) errors.fileSize = 'File size must be non-negative.';
    if (!formData.mimeType.trim()) errors.mimeType = 'MIME type is required.';
    if (!formData.uploadDate) errors.uploadDate = 'Upload date is required.';
    if (!formData.status.trim()) errors.status = 'Status is required.';
    if (formData.chunkCount < 0) errors.chunkCount = 'Chunk count must be non-negative.';
    if (!formData.sessionId.trim()) errors.sessionId = 'Session ID is required.';

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'fileSize' || name === 'chunkCount' ? Number(value) : value,
    }));
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    try {
      if (isEditMode) {
        await updateFileUpload(id!, formData);
      } else {
        await createFileUpload(formData);
      }
      navigate('/file-upload');
    } catch (err) {
      setError(isEditMode ? 'Failed to update file upload.' : 'Failed to create file upload.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        {isEditMode ? 'Edit File Upload' : 'Create New File Upload'}
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="filename">
              Filename *
            </label>
            <input
              type="text"
              id="filename"
              name="filename"
              value={formData.filename}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.filename ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter filename"
            />
            {validationErrors.filename && <p className="text-red-500 text-sm mt-1">{validationErrors.filename}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="originalName">
              Original Name *
            </label>
            <input
              type="text"
              id="originalName"
              name="originalName"
              value={formData.originalName}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.originalName ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter original name"
            />
            {validationErrors.originalName && <p className="text-red-500 text-sm mt-1">{validationErrors.originalName}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="fileSize">
              File Size (bytes) *
            </label>
            <input
              type="number"
              id="fileSize"
              name="fileSize"
              value={formData.fileSize}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.fileSize ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter file size"
              min="0"
            />
            {validationErrors.fileSize && <p className="text-red-500 text-sm mt-1">{validationErrors.fileSize}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="mimeType">
              MIME Type *
            </label>
            <input
              type="text"
              id="mimeType"
              name="mimeType"
              value={formData.mimeType}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.mimeType ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="e.g., application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            />
            {validationErrors.mimeType && <p className="text-red-500 text-sm mt-1">{validationErrors.mimeType}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="uploadDate">
              Upload Date *
            </label>
            <input
              type="date"
              id="uploadDate"
              name="uploadDate"
              value={formData.uploadDate}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.uploadDate ? 'border-red-500' : 'border-gray-300'}`}
            />
            {validationErrors.uploadDate && <p className="text-red-500 text-sm mt-1">{validationErrors.uploadDate}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="status">
              Status *
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.status ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            {validationErrors.status && <p className="text-red-500 text-sm mt-1">{validationErrors.status}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="chunkCount">
              Chunk Count *
            </label>
            <input
              type="number"
              id="chunkCount"
              name="chunkCount"
              value={formData.chunkCount}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.chunkCount ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter chunk count"
              min="0"
            />
            {validationErrors.chunkCount && <p className="text-red-500 text-sm mt-1">{validationErrors.chunkCount}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="sessionId">
              Session ID *
            </label>
            <input
              type="text"
              id="sessionId"
              name="sessionId"
              value={formData.sessionId}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.sessionId ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter session ID"
            />
            {validationErrors.sessionId && <p className="text-red-500 text-sm mt-1">{validationErrors.sessionId}</p>}
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8">
          <button
            type="button"
            onClick={() => navigate('/file-upload')}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-2 px-6 rounded-lg transition duration-200"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin h-5 w-5 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {isEditMode ? 'Updating...' : 'Creating...'}
              </span>
            ) : (
              <span>{isEditMode ? 'Update File Upload' : 'Create File Upload'}</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUploadForm;