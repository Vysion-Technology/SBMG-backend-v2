import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Upload, X, AlertCircle, CheckCircle, LogIn } from 'lucide-react';
import { publicApi, adminApi } from '../api';
import type { CreateComplaintRequest, ComplaintType, District, Block, Village, Complaint } from '../types';

interface CreateComplaintForm extends CreateComplaintRequest {
  files?: FileList;
}

const CreateComplaint: React.FC = () => {
  const navigate = useNavigate();
  const [complaintTypes, setComplaintTypes] = useState<ComplaintType[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ success: boolean; data?: Complaint; error?: string } | null>(null);
  const [citizenToken, setCitizenToken] = useState<string | null>(null);

  const { register, handleSubmit, watch, setValue, formState: { errors }, reset } = useForm<CreateComplaintForm>();

  const selectedDistrictId = watch('district_id');
  const selectedBlockId = watch('block_id');

  // Check for citizen authentication
  useEffect(() => {
    const token = localStorage.getItem('citizen_token');
    setCitizenToken(token);
  }, []);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [complaintTypesData, districtsData] = await Promise.all([
          adminApi.getComplaintTypes(),
          adminApi.getDistricts(),
        ]);
        setComplaintTypes(complaintTypesData);
        setDistricts(districtsData);
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    };
    loadInitialData();
  }, []);

  // Load blocks when district changes
  useEffect(() => {
    if (selectedDistrictId) {
      adminApi.getBlocks(Number(selectedDistrictId))
        .then(setBlocks)
        .catch(console.error);
      setValue('block_id', 0);
      setValue('village_id', 0);
    }
  }, [selectedDistrictId, setValue]);

  // Load villages when block changes
  useEffect(() => {
    if (selectedBlockId) {
      adminApi.getVillages(Number(selectedBlockId))
        .then(setVillages)
        .catch(console.error);
      setValue('village_id', 0);
    }
  }, [selectedBlockId, setValue]);

  const onSubmit = async (data: CreateComplaintForm) => {
    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      const complaintData: CreateComplaintRequest = {
        complaint_type_id: Number(data.complaint_type_id),
        village_id: Number(data.village_id),
        block_id: Number(data.block_id),
        district_id: Number(data.district_id),
        description: data.description,
        mobile_number: data.mobile_number || null,
      };

      let result: Complaint;
      
      if (selectedFiles && selectedFiles.length > 0) {
        result = await publicApi.createComplaintWithMedia(complaintData, selectedFiles);
      } else {
        result = await publicApi.createComplaint(complaintData);
      }

      setSubmitResult({ success: true, data: result });
      reset();
      setSelectedFiles(null);
    } catch (error: any) {
      console.error('Error submitting complaint:', error);
      setSubmitResult({ 
        success: false, 
        error: error.response?.data?.detail || 'Failed to submit complaint. Please try again.' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setSelectedFiles(files);
    }
  };

  const removeFile = (index: number) => {
    if (selectedFiles) {
      const newFiles = Array.from(selectedFiles).filter((_, i) => i !== index);
      const dt = new DataTransfer();
      newFiles.forEach(file => dt.items.add(file));
      setSelectedFiles(dt.files);
    }
  };

  if (submitResult?.success) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="text-green-600 mr-3" size={24} />
            <h2 className="text-lg font-semibold text-green-900">Complaint Submitted Successfully!</h2>
          </div>
          <div className="text-green-800">
            <p className="mb-2">Your complaint has been registered with ID: <strong>#{submitResult.data?.id}</strong></p>
            <p className="mb-2">Status: <strong>{submitResult.data?.status_name}</strong></p>
            <p className="mb-4">You can track the progress using the complaint ID.</p>
            <div className="flex space-x-4">
              <button
                onClick={() => setSubmitResult(null)}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
              >
                Create Another Complaint
              </button>
              <button
                onClick={() => window.location.href = `/complaint-status?id=${submitResult.data?.id}`}
                className="bg-white text-green-600 border border-green-600 px-4 py-2 rounded-md hover:bg-green-50 transition-colors"
              >
                Track Status
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!citizenToken) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-6 py-8 text-center">
            <LogIn className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
            <p className="text-gray-600 mb-6">
              Please login with your mobile number to create a complaint.
            </p>
            <button
              onClick={() => navigate('/citizen-login')}
              className="bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Login to Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Create New Complaint</h1>
          <p className="text-gray-600 mt-1">
            Report issues related to sanitation, infrastructure, or other civic problems.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Complaint Type */}
          <div>
            <label htmlFor="complaint_type_id" className="block text-sm font-medium text-gray-700 mb-1">
              Complaint Type <span className="text-red-500">*</span>
            </label>
            <select
              {...register('complaint_type_id', { required: 'Please select a complaint type' })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select complaint type...</option>
              {complaintTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            {errors.complaint_type_id && (
              <p className="text-red-500 text-sm mt-1">{errors.complaint_type_id.message}</p>
            )}
          </div>

          {/* District */}
          <div>
            <label htmlFor="district_id" className="block text-sm font-medium text-gray-700 mb-1">
              District <span className="text-red-500">*</span>
            </label>
            <select
              {...register('district_id', { required: 'Please select a district' })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select district...</option>
              {districts.map((district) => (
                <option key={district.id} value={district.id}>
                  {district.name}
                </option>
              ))}
            </select>
            {errors.district_id && (
              <p className="text-red-500 text-sm mt-1">{errors.district_id.message}</p>
            )}
          </div>

          {/* Block */}
          <div>
            <label htmlFor="block_id" className="block text-sm font-medium text-gray-700 mb-1">
              Block <span className="text-red-500">*</span>
            </label>
            <select
              {...register('block_id', { required: 'Please select a block' })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              disabled={!selectedDistrictId}
            >
              <option value="">Select block...</option>
              {blocks.map((block) => (
                <option key={block.id} value={block.id}>
                  {block.name}
                </option>
              ))}
            </select>
            {errors.block_id && (
              <p className="text-red-500 text-sm mt-1">{errors.block_id.message}</p>
            )}
          </div>

          {/* Village */}
          <div>
            <label htmlFor="village_id" className="block text-sm font-medium text-gray-700 mb-1">
              Village <span className="text-red-500">*</span>
            </label>
            <select
              {...register('village_id', { required: 'Please select a village' })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              disabled={!selectedBlockId}
            >
              <option value="">Select village...</option>
              {villages.map((village) => (
                <option key={village.id} value={village.id}>
                  {village.name}
                </option>
              ))}
            </select>
            {errors.village_id && (
              <p className="text-red-500 text-sm mt-1">{errors.village_id.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              {...register('description', { 
                required: 'Please provide a description',
                minLength: { value: 10, message: 'Description must be at least 10 characters long' }
              })}
              rows={4}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Provide a detailed description of the issue..."
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          {/* Mobile Number */}
          <div>
            <label htmlFor="mobile_number" className="block text-sm font-medium text-gray-700 mb-1">
              Mobile Number (Optional)
            </label>
            <input
              type="tel"
              {...register('mobile_number', { 
                pattern: { 
                  value: /^[+]?[\d\s-()]+$/,
                  message: 'Please enter a valid mobile number'
                },
                minLength: {
                  value: 10,
                  message: 'Mobile number must be at least 10 digits long'
                }
              })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter your mobile number (e.g., +91 9876543210)"
            />
            {errors.mobile_number && (
              <p className="text-red-500 text-sm mt-1">{errors.mobile_number.message}</p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              This will help us contact you for updates on your complaint
            </p>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Upload Images (Optional)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-md p-6">
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-indigo-600 hover:text-indigo-500">
                        Click to upload
                      </span>{' '}
                      or drag and drop
                    </p>
                    <p className="text-xs text-gray-500">PNG, JPG, JPEG up to 10MB each</p>
                  </div>
                </div>
              </label>
            </div>

            {/* Selected Files */}
            {selectedFiles && selectedFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Selected Files:</p>
                <div className="space-y-2">
                  {Array.from(selectedFiles).map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {submitResult?.error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="text-red-400 mr-3 mt-0.5" size={20} />
                <p className="text-red-800">{submitResult.error}</p>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Complaint'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateComplaint;