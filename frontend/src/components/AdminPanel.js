import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { secureStorage } from '../utils/secureStorage';

const AdminPanel = ({ onClose }) => {
  const [projects, setProjects] = useState([]);
  const [editingProject, setEditingProject] = useState(null);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    base_address: '',
    website: '',
    twitter: '',
    logo_url: ''
  });
  const [loading, setLoading] = useState(false);

  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${API}/admin/projects`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      alert('Failed to load projects. Please check your admin credentials.');
    }
  };

  const handleSaveProject = async () => {
    if (!newProject.name || !newProject.description || !newProject.base_address) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      if (editingProject) {
        await axios.put(`${API}/admin/projects/${editingProject.id}`, newProject, { headers });
      } else {
        await axios.post(`${API}/admin/projects`, newProject, { headers });
      }
      
      setNewProject({
        name: '',
        description: '',
        base_address: '',
        website: '',
        twitter: '',
        logo_url: ''
      });
      setEditingProject(null);
      fetchProjects();
    } catch (error) {
      console.error('Failed to save project:', error);
      alert('Failed to save project. Please try again.');
    }
    setLoading(false);
  };

  const handleEditProject = (project) => {
    setEditingProject(project);
    setNewProject({
      name: project.name || '',
      description: project.description || '',
      base_address: project.base_address || '',
      website: project.website || '',
      twitter: project.twitter || '',
      logo_url: project.logo_url || ''
    });
  };

  const handleDeleteProject = async (projectId) => {
    if (!confirm('Are you sure you want to delete this project?')) {
      return;
    }

    try {
      const token = localStorage.getItem('admin_token');
      await axios.delete(`${API}/admin/projects/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      fetchProjects();
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('Failed to delete project. Please try again.');
    }
  };

  const handleStartContest = async (projectId) => {
    try {
      const token = localStorage.getItem('admin_token');
      await axios.post(`${API}/admin/contest/start`, { project_id: projectId }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      alert('Contest started successfully!');
      fetchProjects();
    } catch (error) {
      console.error('Failed to start contest:', error);
      alert('Failed to start contest. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="silver-glass rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Admin Panel - Community Pool Management</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {/* Add/Edit Project Form */}
        <div className="mb-8 p-4 bg-gray-800 rounded-lg">
          <h3 className="text-xl font-semibold text-white mb-4">
            {editingProject ? 'Edit Project' : 'Add New Project'}
          </h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 mb-1">Project Name *</label>
              <input
                type="text"
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                value={newProject.name}
                onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                placeholder="Enter project name"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 mb-1">Base Address *</label>
              <input
                type="text"
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                value={newProject.base_address}
                onChange={(e) => setNewProject({...newProject, base_address: e.target.value})}
                placeholder="0x..."
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-gray-300 mb-1">Description *</label>
              <textarea
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 h-20"
                value={newProject.description}
                onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                placeholder="Describe the project"
              />
            </div>
            
            <div>
              <label className="block text-gray-300 mb-1">Website</label>
              <input
                type="url"
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                value={newProject.website}
                onChange={(e) => setNewProject({...newProject, website: e.target.value})}
                placeholder="https://..."
              />
            </div>
            
            <div>
              <label className="block text-gray-300 mb-1">Twitter</label>
              <input
                type="text"
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                value={newProject.twitter}
                onChange={(e) => setNewProject({...newProject, twitter: e.target.value})}
                placeholder="@username"
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-gray-300 mb-1">Logo URL</label>
              <input
                type="url"
                className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
                value={newProject.logo_url}
                onChange={(e) => setNewProject({...newProject, logo_url: e.target.value})}
                placeholder="https://..."
              />
            </div>
          </div>
          
          <div className="flex gap-3 mt-4">
            {editingProject && (
              <button 
                onClick={() => {
                  setEditingProject(null);
                  setNewProject({
                    name: '', description: '', base_address: '', 
                    website: '', twitter: '', logo_url: ''
                  });
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Cancel Edit
              </button>
            )}
            <button 
              onClick={handleSaveProject}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (editingProject ? 'Update Project' : 'Add Project')}
            </button>
          </div>
        </div>

        {/* Projects List */}
        <div>
          <h3 className="text-xl font-semibold text-white mb-4">Manage Projects</h3>
          <div className="space-y-4">
            {projects.map((project) => (
              <div key={project.id || project._id} className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-white">{project.name}</h4>
                    <p className="text-gray-300 mb-2">{project.description}</p>
                    <div className="grid md:grid-cols-2 gap-2 text-sm">
                      <p><span className="text-gray-400">Address:</span> {project.base_address}</p>
                      <p><span className="text-gray-400">Twitter:</span> {project.twitter || 'N/A'}</p>
                      <p><span className="text-gray-400">Website:</span> 
                        {project.website ? (
                          <a href={project.website} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                            {project.website}
                          </a>
                        ) : 'N/A'}
                      </p>
                      <p><span className="text-gray-400">Status:</span> 
                        <span className={`ml-1 px-2 py-1 rounded text-xs ${
                          project.is_active ? 'bg-green-600' : 'bg-gray-600'
                        }`}>
                          {project.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 ml-4">
                    <button 
                      onClick={() => handleEditProject(project)}
                      className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => handleStartContest(project.id)}
                      className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                    >
                      Start Contest
                    </button>
                    <button 
                      onClick={() => handleDeleteProject(project.id)}
                      className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;