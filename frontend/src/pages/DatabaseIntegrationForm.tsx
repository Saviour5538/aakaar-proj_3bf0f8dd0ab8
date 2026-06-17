import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDatabaseIntegration, createDatabaseIntegration, updateDatabaseIntegration } from '../api/client';

interface DatabaseIntegrationFormData {
  name: string;
  connection_string: string;
  database_type: string;
  description: string;
  is_active: boolean;
}

const DatabaseIntegrationForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const [formData, setFormData] = useState<DatabaseIntegrationFormData>({
    name: '',
    connection_string: '',
    database_type: 'postgresql',
    description: '',
    is_active: true,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isEditMode && id) {
      fetchDatabaseIntegration(id);
    }
  }, [id, isEditMode]);

  const fetchDatabaseIntegration = async (integrationId: string) => {
    try {
      setLoading(true);
      const data = await getDatabaseIntegration(integrationId);
      setFormData({
        name: data.name,
        connection_string: data.connection_string,
        database_type: data.database_type,
        description: data.description,
        is_active: data.is_active,
      });
      setError('');
    } catch (err) {
      setError('Failed to load database integration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }

    if (!formData.connection_string.trim()) {
      errors.connection_string = 'Connection string is required';
    }

    if (!formData.database_type.trim()) {
      errors.database_type = 'Database type is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      if (isEditMode && id) {
        await updateDatabaseIntegration(id, formData);
      } else {
        await createDatabaseIntegration(formData);
      }
      navigate('/database-integrations');
    } catch (err) {
      setError('Failed to save database integration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEditMode) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        {isEditMode ? 'Edit Database Integration' : 'Create New Database Integration'}
      </h1>

      {error && (
        <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.name ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter integration name"
            />
            {validationErrors.name && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="connection_string" className="block text-sm font-medium text-gray-700 mb-1">
              Connection String *
            </label>
            <textarea
              id="connection_string"
              name="connection_string"
              value={formData.connection_string}
              onChange={handleChange}
              rows={3}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.connection_string ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="Enter database connection string"
            />
            {validationErrors.connection_string && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.connection_string}</p>
            )}
          </div>

          <div>
            <label htmlFor="database_type" className="block text-sm font-medium text-gray-700 mb-1">
              Database Type *
            </label>
            <select
              id="database_type"
              name="database_type"
              value={formData.database_type}
              onChange={handleChange}
              className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${validationErrors.database_type ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="mongodb">MongoDB</option>
              <option value="redis">Redis</option>
            </select>
            {validationErrors.database_type && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.database_type}</p>
            )}
          </div>

          <div>
            <label htmlFor="is_active" className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Active</span>
            </label>
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              placeholder="Enter description (optional)"
            />
          </div>
        </div>

        <div className="mt-8 flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/database-integrations')}
            className="px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition duration-200"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </span>
            ) : (
              isEditMode ? 'Update Integration' : 'Create Integration'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DatabaseIntegrationForm;