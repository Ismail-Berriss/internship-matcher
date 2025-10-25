import React, { useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

function App() {
    const [file, setFile] = useState(null);
    const [fields, setFields] = useState([]);
    const [selectedField, setSelectedField] = useState(''); // Hold a single field string
    const [jobs, setJobs] = useState([]);
    const [step, setStep] = useState(1); // 1: upload, 2: select field & location, 3: show jobs
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [location, setLocation] = useState(''); // Default to empty string for "All Locations"
    const [isAnimating, setIsAnimating] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    // Step 1: Upload CV
    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setError('');
    };

    // Drag and drop handlers
    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            if (
                droppedFile.type === 'application/pdf' ||
                droppedFile.type ===
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                droppedFile.type === 'application/msword'
            ) {
                setFile(droppedFile);
                setError('');
            } else {
                setError('Please upload a PDF or DOCX file.');
            }
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a CV file (PDF or DOCX).');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        setLoading(true);
        setError('');
        setIsAnimating(true);

        try {
            const res = await fetch(`${API_BASE}/upload-cv`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'Failed to analyze CV');
            }

            const data = await res.json();
            setFields(data.fields || []);
            setTimeout(() => {
                setStep(2);
                setIsAnimating(false);
            }, 500);
        } catch (err) {
            setError(err.message || 'Upload failed');
            setIsAnimating(false);
        } finally {
            setLoading(false);
        }
    };

    // Update selected field
    const handleFieldChange = (field) => {
        setSelectedField(field);
    };

    // Step 2: Search internships
    const handleSearch = async () => {
        if (!selectedField) {
            setError('Please select a field.');
            return;
        }

        setLoading(true);
        setError('');
        setIsAnimating(true);

        try {
            // Send the selected field as a single-item array to match backend expectation
            const profile = {
                field: selectedField, // Backend expects an array
                skills: [],
                level: 'Student',
                location: location,
            };

            const res = await fetch(`${API_BASE}/scrape-internships`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profile),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(
                    errorData.detail || 'Failed to fetch internships'
                );
            }

            const data = await res.json();
            setJobs(data.jobs || []);
            setTimeout(() => {
                setStep(3);
                setIsAnimating(false);
            }, 500);
        } catch (err) {
            setError(err.message || 'Scraping failed');
            setIsAnimating(false);
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setIsAnimating(true);
        setTimeout(() => {
            setFile(null);
            setFields([]);
            setSelectedField('');
            setJobs([]);
            setStep(1);
            setError('');
            setLocation('');
            setIsAnimating(false);
        }, 300);
    };

    // Function to render a loading spinner
    const renderSpinner = () => (
        <div className="spinner">
            <div className="spinner-dot"></div>
            <div className="spinner-dot"></div>
            <div className="spinner-dot"></div>
        </div>
    );

    return (
        <div className="app">
            <div className={`container ${isAnimating ? 'animating' : ''}`}>
                <h1 className="title">
                    <span className="gradient-text">Internship Matcher</span>
                    <span className="emoji">🎓</span>
                </h1>

                {error && <div className="error">{error}</div>}

                {step === 1 && (
                    <div className="card">
                        <h2>Upload Your CV</h2>
                        <p className="card-description">
                            Upload your CV to get personalized internship
                            recommendations based on your skills and experience.
                        </p>
                        <div
                            className={`file-input ${
                                dragActive ? 'drag-active' : ''
                            } ${file ? 'has-file' : ''}`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <input
                                type="file"
                                accept=".pdf,.docx,.doc"
                                onChange={handleFileChange}
                                disabled={loading}
                                style={{ display: 'none' }}
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="file-label">
                                {file ? (
                                    <div className="file-info">
                                        <span className="file-icon">✅</span>
                                        <span className="file-name">
                                            {file.name}
                                        </span>
                                        <span className="file-size">
                                            (
                                            {(file.size / 1024 / 1024).toFixed(
                                                2
                                            )}{' '}
                                            MB)
                                        </span>
                                    </div>
                                ) : (
                                    <div className="file-placeholder">
                                        <span className="upload-icon">📁</span>
                                        <span className="upload-text">
                                            {dragActive
                                                ? 'Drop your CV here'
                                                : 'Click to browse or drag & drop your CV'}
                                        </span>
                                        <span className="upload-hint">
                                            PDF, DOCX up to 10MB
                                        </span>
                                    </div>
                                )}
                            </label>
                        </div>
                        <button
                            onClick={handleUpload}
                            disabled={loading || !file}
                            className="btn btn-primary"
                        >
                            {loading ? renderSpinner() : 'Upload & Analyze'}
                        </button>
                    </div>
                )}

                {step === 2 && (
                    <div className="card">
                        <h2>Select Field & Location</h2>
                        <p className="card-description">
                            We found these fields in your CV. Choose your
                            primary field and preferred location for
                            internships.
                        </p>

                        {/* Field Selection Section - Now using Radio Buttons */}
                        <div className="section">
                            <h3>Field</h3>
                            <div className="field-list">
                                {fields.map((field, idx) => (
                                    <label
                                        key={idx}
                                        className={`field-item ${
                                            selectedField === field
                                                ? 'selected'
                                                : ''
                                        }`}
                                    >
                                        <input
                                            type="radio"
                                            name="selectedField"
                                            checked={selectedField === field}
                                            onChange={() =>
                                                handleFieldChange(field)
                                            }
                                        />
                                        <span className="field-content">
                                            <span className="field-name">
                                                {field}
                                            </span>
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Location Selection Section */}
                        <div className="section">
                            <h3>Location</h3>
                            <select
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                className="location-select"
                                disabled={loading}
                            >
                                <option value="">🌐 All Locations</option>
                                <option value="Morocco">🇲🇦 Morocco</option>
                                <option value="France">🇫🇷 France</option>
                            </select>
                        </div>

                        <div className="button-group">
                            <button
                                onClick={() => setStep(1)}
                                className="btn btn-secondary"
                                disabled={loading}
                            >
                                Back
                            </button>
                            <button
                                onClick={handleSearch}
                                disabled={loading || !selectedField}
                                className="btn btn-success"
                            >
                                {loading ? renderSpinner() : 'Find Internships'}
                            </button>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="card">
                        <div className="header-with-reset">
                            <h2>Found {jobs.length} Internships</h2>
                            <button onClick={reset} className="btn-link">
                                🔄 Start Over
                            </button>
                        </div>

                        {loading ? ( // Show spinner while loading jobs
                            <div className="loading-jobs">
                                {renderSpinner()}
                                <p>Searching for the best internships...</p>
                            </div>
                        ) : jobs.length === 0 ? (
                            <div className="no-results">
                                <h3>No Internships Found</h3>
                                <p>
                                    We couldn't find any internships for "
                                    <strong>{selectedField}</strong>" in "
                                    <strong>
                                        {location || 'All Locations'}
                                    </strong>
                                    ".
                                </p>
                                <p>
                                    Try adjusting your field or location
                                    preferences.
                                </p>
                            </div>
                        ) : (
                            <div className="job-list">
                                {jobs.map((job, idx) => (
                                    <div key={idx} className="job-card">
                                        <div className="job-header">
                                            <h3>{job.title}</h3>
                                            <div className="job-badge">New</div>
                                        </div>
                                        <p className="company">
                                            <span className="company-icon">
                                                🏢
                                            </span>
                                            {job.company}
                                        </p>
                                        <p className="location">
                                            {job.location || 'Remote'} •{' '}
                                            {job.source == 'wttj'
                                                ? 'Welcome To The Jungle'
                                                : 'LinkedIn'}
                                        </p>
                                        <a
                                            href={job.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="job-link"
                                        >
                                            Apply Now
                                        </a>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
