import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getChunkingStrategy, createChunkingStrategy, updateChunkingStrategy, ChunkingStrategy } from '../api/client';

const ChunkingStrategyForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = !!id;

  const [formData, setFormData] = useState<Omit<ChunkingStrategy, 'id' | 'createdAt'>>({
    name: '',
    description: '',
    chunkSize: 1000,
    overlapPercentage: 20,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isEditMode) {
      const fetchData = async () => {
        try {
          setLoading(true);
          const data = await getChunkingStrategy(id);
          setFormData({
            name: data.name,
            description: data.description,
            chunkSize: data.chunkSize,
            overlapPercentage: data.overlapPercentage,
          });
          setError(null);
        } catch (err) {
          setError('Failed to load chunking strategy');
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [id, isEditMode]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.name.trim()) errors.name = 'Name is required';
    if (formData.chunkSize <= 0) errors.chunkSize = 'Chunk size must be positive';
    if (formData.overlapPercentage < 0 || formData.overlapPercentage > 100) errors.overlapPercentage = 'Overlap must be between 0 and 100';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setLoading(true);
      if (isEditMode) {
        await updateChunkingStrategy(id, formData);
      } else {
        await createChunkingStrategy(formData);
      }
      navigate('/chunking-strategy');
    } catch (err) {
      setError('Failed to save chunking strategy');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'chunkSize' || name === 'overlapPercentage' ? Number(value) : value,
    }));
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">
        {isEditMode ? 'Edit Chunking Strategy' : 'Create New Chunking Strategy'}
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
            Strategy Name *
          </label>
          <input
            id="name"
            name="name"
            type="text"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${validationErrors.name ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}`}
            value={formData.name}
            onChange={handleChange}
            disabled={loading}
          />
          {validationErrors.name && <p className="text-red-500 text-xs mt-1">{validationErrors.name}</p>}
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.description}
            onChange={handleChange}
            disabled={loading}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="chunkSize">
              Chunk Size *
            </label>
            <input
              id="chunkSize"
              name="chunkSize"
              type="number"
              min="1"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${validationErrors.chunkSize ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}`}
              value={formData.chunkSize}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.chunkSize && <p className="text-red-500 text-xs mt-1">{validationErrors.chunkSize}</p>}
            <p className="text-gray-500 text-xs mt-1">Number of characters per chunk</p>
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="overlapPercentage">
              Overlap Percentage *
            </label>
            <input
              id="overlapPercentage"
              name="overlapPercentage"
              type="number"
              min="0"
              max="100"
              step="1"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${validationErrors.overlapPercentage ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}`}
              value={formData.overlapPercentage}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.overlapPercentage && <p className="text-red-500 text-xs mt-1">{validationErrors.overlapPercentage}</p>}
            <p className="text-gray-500 text-xs mt-1">Percentage overlap between chunks (0-100)</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-6">
          <button
            type="button"
            onClick={() => navigate('/chunking-strategy')}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-2 px-4 rounded-lg transition duration-200"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </span>
            ) : (
              isEditMode ? 'Update Strategy' : 'Create Strategy'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChunkingStrategyForm;