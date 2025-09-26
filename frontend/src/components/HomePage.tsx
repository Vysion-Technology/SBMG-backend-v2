import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Search, Users, ChevronRight } from 'lucide-react';

const HomePage: React.FC = () => {
  return (
    <div className="px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Swachh Bharat Mission - Gramin Rajasthan
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          A comprehensive complaint management system to help maintain cleanliness and sanitation in rural Rajasthan. 
          Submit complaints, track progress, and stay informed about community improvements.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <ActionCard
          to="/create-complaint"
          icon={<FileText size={24} />}
          title="Create Complaint"
          description="Report issues related to sanitation, water supply, roads, and more"
          color="bg-blue-50 border-blue-200 hover:bg-blue-100"
          iconColor="text-blue-600"
        />
        <ActionCard
          to="/complaint-status"
          icon={<Search size={24} />}
          title="Check Status"
          description="Track the progress of your complaint using complaint ID"
          color="bg-green-50 border-green-200 hover:bg-green-100"
          iconColor="text-green-600"
        />
        <ActionCard
          to="/login"
          icon={<Users size={24} />}
          title="Staff Login"
          description="Access staff dashboard for complaint management and reporting"
          color="bg-purple-50 border-purple-200 hover:bg-purple-100"
          iconColor="text-purple-600"
        />
      </div>

      {/* Features Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Key Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <FeatureItem
            title="Public Complaint Creation"
            description="Anyone can create complaints without authentication"
          />
          <FeatureItem
            title="Automatic Assignment"
            description="Complaints get assigned to workers based on location"
          />
          <FeatureItem
            title="Status Tracking"
            description="Complete workflow from creation to completion and verification"
          />
          <FeatureItem
            title="Media Support"
            description="Upload images to provide visual evidence of issues"
          />
        </div>
      </div>

      {/* Information Section */}
      <div className="mt-12 bg-gray-50 rounded-lg p-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          How it Works
        </h2>
        <div className="space-y-4">
          <Step
            number="1"
            title="Submit Complaint"
            description="Create a complaint with details about the issue and optional images"
          />
          <Step
            number="2"
            title="Automatic Assignment"
            description="The system assigns your complaint to the appropriate worker based on location"
          />
          <Step
            number="3"
            title="Work Progress"
            description="Track the progress as workers update the status and complete the work"
          />
          <Step
            number="4"
            title="Verification"
            description="Local officers verify the completed work and close the complaint"
          />
        </div>
      </div>
    </div>
  );
};

interface ActionCardProps {
  to: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  iconColor: string;
}

const ActionCard: React.FC<ActionCardProps> = ({ to, icon, title, description, color, iconColor }) => (
  <Link
    to={to}
    className={`block p-6 border-2 rounded-lg transition-all duration-200 ${color}`}
  >
    <div className="flex items-center justify-between">
      <div className={`p-3 rounded-full bg-white ${iconColor}`}>
        {icon}
      </div>
      <ChevronRight className="text-gray-400" size={20} />
    </div>
    <h3 className="font-semibold text-gray-900 mt-4 mb-2">{title}</h3>
    <p className="text-gray-600 text-sm">{description}</p>
  </Link>
);

interface FeatureItemProps {
  title: string;
  description: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ title, description }) => (
  <div className="text-center">
    <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 text-sm">{description}</p>
  </div>
);

interface StepProps {
  number: string;
  title: string;
  description: string;
}

const Step: React.FC<StepProps> = ({ number, title, description }) => (
  <div className="flex items-start">
    <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-semibold mr-4">
      {number}
    </div>
    <div>
      <h4 className="font-semibold text-gray-900 mb-1">{title}</h4>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  </div>
);

export default HomePage;