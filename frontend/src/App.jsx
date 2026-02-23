import React, { useState } from 'react';
import axios from 'axios';
import { Play, Loader2 } from 'lucide-react';

function App() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });

  const [formData, setFormData] = useState({
    groq_api_key: '',
    linkedin_email: '',
    linkedin_password: '',
    cv_path: '',
    salary_expectation: '',
    location: '',
    commuting: '',
    veteran_status: 'No',
    disability: 'No',
    ethnicity: '',
    gender: 'Male',
    address: '',
    zip_code: '',
    middle_name: '',
    phone: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'salary_expectation' ? parseInt(value) || '' : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: '', message: '' });
    try {
      await axios.post('http://localhost:8000/api/start', formData);
      setStatus({ type: 'success', message: 'Agent started — watch your terminal for live logs.' });
    } catch (err) {
      setStatus({ type: 'error', message: 'Could not reach backend. Is server.py running?' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="root">
      {/* Header */}
      <div className="header">
        <div className="header-badge">
          <span className="dot" />
          Agentic AI
        </div>
        <h1>AutoBot</h1>
        <p>Agentic AI Job Applicator · Powered by Groq</p>
      </div>

      <form onSubmit={handleSubmit}>

        {/* Credentials */}
        <div className="section">
          <div className="section-label">Credentials</div>
          <div className="grid">
            <div className="field full">
              <label>Groq API Key</label>
              <input type="password" name="groq_api_key" value={formData.groq_api_key}
                onChange={handleChange} placeholder="gsk_..." required />
            </div>
            <div className="field">
              <label>LinkedIn Email</label>
              <input type="email" name="linkedin_email" value={formData.linkedin_email}
                onChange={handleChange} placeholder="you@example.com" required />
            </div>
            <div className="field">
              <label>LinkedIn Password</label>
              <input type="password" name="linkedin_password" value={formData.linkedin_password}
                onChange={handleChange} placeholder="••••••••" required />
            </div>
            <div className="field full">
              <label>CV / Resume Path</label>
              <input type="text" name="cv_path" value={formData.cv_path}
                onChange={handleChange} placeholder="C:\Users\Name\Documents\Resume.pdf" required />
            </div>
          </div>
        </div>

        {/* Profile */}
        <div className="section">
          <div className="section-label">Profile</div>
          <div className="grid">
            <div className="field">
              <label>Phone</label>
              <input type="tel" name="phone" value={formData.phone}
                onChange={handleChange} placeholder="e.g. 5551234567" required />
            </div>
            <div className="field">
              <label>Middle Name</label>
              <input type="text" name="middle_name" value={formData.middle_name}
                onChange={handleChange} placeholder="e.g. A" />
            </div>
            <div className="field full">
              <label>Full Address</label>
              <input type="text" name="address" value={formData.address}
                onChange={handleChange} placeholder="123 Main St, City, State, US" required />
            </div>
            <div className="field">
              <label>Location</label>
              <input type="text" name="location" value={formData.location}
                onChange={handleChange} placeholder="City, State" required />
            </div>
            <div className="field">
              <label>Zip Code</label>
              <input type="text" name="zip_code" value={formData.zip_code}
                onChange={handleChange} placeholder="e.g. 10001" required />
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="section">
          <div className="section-label">Preferences</div>
          <div className="grid">
            <div className="field">
              <label>Salary Expectation (USD)</label>
              <input type="number" name="salary_expectation" value={formData.salary_expectation}
                onChange={handleChange} placeholder="e.g. 75000" required />
            </div>
            <div className="field">
              <label>Commuting To</label>
              <input type="text" name="commuting" value={formData.commuting}
                onChange={handleChange} placeholder="e.g. New York City" required />
            </div>
            <div className="field">
              <label>Gender</label>
              <select name="gender" value={formData.gender} onChange={handleChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-binary">Non-binary</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>
            <div className="field">
              <label>Veteran Status</label>
              <select name="veteran_status" value={formData.veteran_status} onChange={handleChange}>
                <option value="No">No</option>
                <option value="Yes">Yes</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>
            <div className="field">
              <label>Disability Status</label>
              <select name="disability" value={formData.disability} onChange={handleChange}>
                <option value="No">No</option>
                <option value="Yes">Yes</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>
            <div className="field">
              <label>Ethnicity</label>
              <input type="text" name="ethnicity" value={formData.ethnicity}
                onChange={handleChange} placeholder="e.g. Hispanic or Latino" />
            </div>
          </div>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading
            ? <><Loader2 size={16} className="spin" /> Initializing Agent…</>
            : <><Play size={16} /> Start Automation</>}
        </button>

        {status.message && (
          <div className={`status ${status.type}`}>{status.message}</div>
        )}
      </form>

      <div className="footer">
        ⚠️ For educational &amp; research purposes only.<br />
        Automated job applications violate LinkedIn's Terms of Service.
      </div>
    </div>
  );
}

export default App;
