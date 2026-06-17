import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getFileUploads, deleteFileUpload } from '../api/client';

interface FileUpload {
  id: string;
  filename: string;
  originalName: string;
  fileSize: number;
  mimeType: string;
  uploadDate: string;
  status: string;
  chunkCount: number;
  sessionId: string;
}

const FileUploadList: React.FC = () => {
  const [items, setItems] = useState<FileUpload[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>('');

  useEffect(() => {
    fetchFileUploads();
  }, []);

  const fetchFileUploads = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFileUploads();
      setItems(data);
    } catch (err) {
      setError('Failed to load file uploads.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this file upload?')) {
      try {
        await deleteFileUpload(id);
        fetchFileUploads();
      } catch (err) {
        setError('Failed to delete file upload.');
        console.error(err);
      }
    }
  };

  const filteredItems = items.filter(item =>
    item.filename.toLowerCase().includes(search.toLowerCase()) ||
    item.originalName.toLowerCase().includes(search.toLowerCase()) ||
    item.status.toLowerCase().includes(search.toLowerCase()) ||
    item.sessionId.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">File Uploads</h1>
        <Link
          to="/file-upload/new"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
        >
          Add New File Upload
        </Link>
      </div>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by filename, original name, status, or session ID..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filename</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Original Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File Size</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MIME Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Upload Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chunk Count</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Session ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.filename}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.originalName}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.fileSize} bytes</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.mimeType}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{new Date(item.uploadDate).toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${item.status === 'completed' ? 'bg-green-100 text-green-800' : item.status === 'processing' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.chunkCount}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{item.sessionId}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      to={`/file-upload/edit/${item.id}`}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredItems.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No file uploads found.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUploadList;