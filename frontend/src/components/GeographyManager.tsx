import React, { useState, useEffect } from 'react';
import { Plus, MapPin, Building, Home, AlertCircle, CheckCircle, X, Loader2 } from 'lucide-react';
import { adminApi } from '../api';
import type { District, Block, Village, CreateDistrictRequest, CreateBlockRequest, CreateVillageRequest } from '../types';

type EntityType = 'district' | 'block' | 'village';

interface FormData {
  name: string;
  description: string;
  district_id: number;
  block_id: number;
}

interface SubmitResult {
  success: boolean;
  message: string;
}

const GeographyManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<EntityType>('district');
  const [districts, setDistricts] = useState<District[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<number>(0);
  const [selectedBlock, setSelectedBlock] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    district_id: 0,
    block_id: 0
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load initial data
  useEffect(() => {
    loadDistricts();
  }, []);

  // Load blocks when district changes
  useEffect(() => {
    if (selectedDistrict > 0) {
      loadBlocks(selectedDistrict);
    } else {
      setBlocks([]);
    }
    setSelectedBlock(0);
  }, [selectedDistrict]);

  // Load villages when block changes
  useEffect(() => {
    if (selectedBlock > 0) {
      loadVillages(selectedBlock);
    } else {
      setVillages([]);
    }
  }, [selectedBlock]);

  const loadDistricts = async () => {
    try {
      setIsLoading(true);
      const data = await adminApi.getDistricts();
      setDistricts(data);
    } catch (error) {
      console.error('Error loading districts:', error);
      setSubmitResult({
        success: false,
        message: 'Failed to load districts'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadBlocks = async (districtId: number) => {
    try {
      setIsLoading(true);
      const data = await adminApi.getBlocks(districtId);
      setBlocks(data);
    } catch (error) {
      console.error('Error loading blocks:', error);
      setSubmitResult({
        success: false,
        message: 'Failed to load blocks'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadVillages = async (blockId: number) => {
    try {
      setIsLoading(true);
      const data = await adminApi.getVillages(blockId);
      setVillages(data);
    } catch (error) {
      console.error('Error loading villages:', error);
      setSubmitResult({
        success: false,
        message: 'Failed to load villages'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (activeTab === 'block' && formData.district_id === 0) {
      newErrors.district_id = 'District is required for blocks';
    }

    if (activeTab === 'village') {
      if (formData.district_id === 0) {
        newErrors.district_id = 'District is required for villages';
      }
      if (formData.block_id === 0) {
        newErrors.block_id = 'Block is required for villages';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      let result: District | Block | Village;
      
      switch (activeTab) {
        case 'district':
          const districtData: CreateDistrictRequest = {
            name: formData.name.trim(),
            description: formData.description.trim() || undefined
          };
          result = await adminApi.createDistrict(districtData);
          setDistricts(prev => [...prev, result as District]);
          break;

        case 'block':
          const blockData: CreateBlockRequest = {
            name: formData.name.trim(),
            description: formData.description.trim() || undefined,
            district_id: formData.district_id
          };
          result = await adminApi.createBlock(blockData);
          setBlocks(prev => [...prev, result as Block]);
          break;

        case 'village':
          const villageData: CreateVillageRequest = {
            name: formData.name.trim(),
            description: formData.description.trim() || undefined,
            block_id: formData.block_id,
            district_id: formData.district_id
          };
          result = await adminApi.createVillage(villageData);
          setVillages(prev => [...prev, result as Village]);
          break;

        default:
          throw new Error('Invalid entity type');
      }

      setSubmitResult({
        success: true,
        message: `${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} created successfully!`
      });
      
      resetForm();
      setShowCreateForm(false);
    } catch (error: any) {
      console.error('Error creating entity:', error);
      setSubmitResult({
        success: false,
        message: error.response?.data?.detail || `Failed to create ${activeTab}`
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      district_id: 0,
      block_id: 0
    });
    setErrors({});
  };

  const handleTabChange = (tab: EntityType) => {
    setActiveTab(tab);
    setShowCreateForm(false);
    resetForm();
    setSubmitResult(null);
  };

  const handleInputChange = (field: keyof FormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const renderEntityList = () => {
    let entities: any[] = [];
    let icon = <MapPin className="w-4 h-4" />;
    
    switch (activeTab) {
      case 'district':
        entities = districts;
        icon = <MapPin className="w-4 h-4" />;
        break;
      case 'block':
        entities = blocks;
        icon = <Building className="w-4 h-4" />;
        break;
      case 'village':
        entities = villages;
        icon = <Home className="w-4 h-4" />;
        break;
    }

    if (isLoading && entities.length === 0) {
      return (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          <span>Loading...</span>
        </div>
      );
    }

    if (entities.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <div className="mb-2">{icon}</div>
          <p>No {activeTab}s found</p>
          {activeTab !== 'district' && (
            <p className="text-sm">
              {activeTab === 'block' ? 'Select a district above' : 'Select a district and block above'}
            </p>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {entities.map((entity) => (
          <div key={entity.id} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {icon}
                <div>
                  <h4 className="font-medium">{entity.name}</h4>
                  {entity.description && (
                    <p className="text-sm text-gray-600">{entity.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">ID: {entity.id}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderCreateForm = () => (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium">
          Create New {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
        </h3>
        <button
          onClick={() => setShowCreateForm(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* District Selection (for blocks and villages) */}
        {(activeTab === 'block' || activeTab === 'village') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              District *
            </label>
            <select
              value={formData.district_id}
              onChange={(e) => {
                const districtId = parseInt(e.target.value);
                handleInputChange('district_id', districtId);
                setSelectedDistrict(districtId);
                if (activeTab === 'village') {
                  handleInputChange('block_id', 0);
                }
              }}
              className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.district_id ? 'border-red-500' : 'border-gray-300'
              }`}
              required
            >
              <option value={0}>Select a district</option>
              {districts.map((district) => (
                <option key={district.id} value={district.id}>
                  {district.name}
                </option>
              ))}
            </select>
            {errors.district_id && (
              <p className="text-red-500 text-sm mt-1">{errors.district_id}</p>
            )}
          </div>
        )}

        {/* Block Selection (for villages) */}
        {activeTab === 'village' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Block *
            </label>
            <select
              value={formData.block_id}
              onChange={(e) => {
                const blockId = parseInt(e.target.value);
                handleInputChange('block_id', blockId);
                setSelectedBlock(blockId);
              }}
              className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.block_id ? 'border-red-500' : 'border-gray-300'
              }`}
              required
              disabled={formData.district_id === 0}
            >
              <option value={0}>Select a block</option>
              {blocks.map((block) => (
                <option key={block.id} value={block.id}>
                  {block.name}
                </option>
              ))}
            </select>
            {errors.block_id && (
              <p className="text-red-500 text-sm mt-1">{errors.block_id}</p>
            )}
          </div>
        )}

        {/* Name Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder={`Enter ${activeTab} name`}
            required
          />
          {errors.name && (
            <p className="text-red-500 text-sm mt-1">{errors.name}</p>
          )}
        </div>

        {/* Description Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description (Optional)
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder={`Enter ${activeTab} description`}
            rows={3}
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-2">
          <button
            type="button"
            onClick={() => setShowCreateForm(false)}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            Create {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Geography Management</h1>
        <p className="text-gray-600">Create and manage districts, blocks, and villages</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6">
        {['district', 'block', 'village'].map((tab) => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab as EntityType)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'district' && <MapPin className="w-4 h-4 inline mr-2" />}
            {tab === 'block' && <Building className="w-4 h-4 inline mr-2" />}
            {tab === 'village' && <Home className="w-4 h-4 inline mr-2" />}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}s
          </button>
        ))}
      </div>

      {/* Filters for Blocks and Villages */}
      {(activeTab === 'block' || activeTab === 'village') && (
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by District
              </label>
              <select
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={0}>All Districts</option>
                {districts.map((district) => (
                  <option key={district.id} value={district.id}>
                    {district.name}
                  </option>
                ))}
              </select>
            </div>
            
            {activeTab === 'village' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filter by Block
                </label>
                <select
                  value={selectedBlock}
                  onChange={(e) => setSelectedBlock(parseInt(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={selectedDistrict === 0}
                >
                  <option value={0}>All Blocks</option>
                  {blocks.map((block) => (
                    <option key={block.id} value={block.id}>
                      {block.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Success/Error Messages */}
      {submitResult && (
        <div className={`mb-6 p-4 rounded-md flex items-center ${
          submitResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {submitResult.success ? (
            <CheckCircle className="w-5 h-5 mr-2" />
          ) : (
            <AlertCircle className="w-5 h-5 mr-2" />
          )}
          {submitResult.message}
          <button
            onClick={() => setSubmitResult(null)}
            className="ml-auto text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && renderCreateForm()}

      {/* Create Button */}
      {!showCreateForm && (
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </button>
        </div>
      )}

      {/* Entity List */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-lg font-medium mb-4">
          {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}s
          {activeTab === 'block' && selectedDistrict > 0 && 
            ` in ${districts.find(d => d.id === selectedDistrict)?.name}`}
          {activeTab === 'village' && selectedBlock > 0 && 
            ` in ${blocks.find(b => b.id === selectedBlock)?.name}`}
        </h2>
        {renderEntityList()}
      </div>
    </div>
  );
};

export default GeographyManager;