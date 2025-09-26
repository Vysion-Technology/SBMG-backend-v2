import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DetailedComplaintView from './DetailedComplaintView';

const ComplaintDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const complaintId = id ? parseInt(id, 10) : 0;

  const handleBack = () => {
    navigate(-1);
  };

  if (!id || isNaN(complaintId)) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Invalid Complaint ID</h2>
          <p className="text-gray-600 mb-4">Please check the URL and try again.</p>
          <button
            onClick={handleBack}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return <DetailedComplaintView complaintId={complaintId} onBack={handleBack} />;
};

export default ComplaintDetailPage;