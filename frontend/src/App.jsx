import React, { useState } from 'react';
import './App.css';

function App() {
    const [file, setFile] = useState(null);
    const [fields, setFields] = useState([]);
    const [selectedField, setSelectedField] = useState(''); // Hold a single field string
    const [jobs, setJobs] = useState([]);
    const [step, setStep] = useState(1); // 1: upload, 2: select field & location, 3: show jobs
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [location, setLocation] = useState(''); // Default to empty string for "All Locations"

    // Step 1: Upload CV
    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
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

        try {
            const res = await fetch('http://localhost:8000/upload-cv', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'Failed to analyze CV');
            }

            const data = await res.json();
            setFields(data.fields || []);
            setStep(2);
        } catch (err) {
            setError(err.message || 'Upload failed');
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

        try {
            // Send the selected field as a single-item array to match backend expectation
            const profile = {
                field: selectedField, // Backend expects an array
                skills: [],
                level: 'Student',
                location: location,
            };

            const res = await fetch(
                'http://localhost:8000/scrape-internships',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profile),
                }
            );

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(
                    errorData.detail || 'Failed to fetch internships'
                );
            }

            const data = await res.json();
            setJobs(data.jobs || []);
            setStep(3);
        } catch (err) {
            setError(err.message || 'Scraping failed');
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setFile(null);
        setFields([]);
        setSelectedField('');
        setJobs([]);
        setStep(1);
        setError('');
        setLocation('');
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
            <div className="container">
                <h1 className="title">Internship Matcher 🎓</h1>

                {error && <div className="error">{error}</div>}

                {step === 1 && (
                    <div className="card">
                        <h2>Upload Your CV</h2>
                        <input
                            type="file"
                            accept=".pdf,.docx,.doc"
                            onChange={handleFileChange}
                            className="file-input"
                            disabled={loading} // Disable input while loading
                        />
                        <button
                            onClick={handleUpload}
                            disabled={loading}
                            className="btn btn-primary"
                        >
                            {loading ? renderSpinner() : 'Upload & Analyze'}
                        </button>
                    </div>
                )}

                {step === 2 && (
                    <div className="card">
                        <h2>Select Field & Location</h2>
                        <p>
                            We found these fields in your CV. Choose one. Also,
                            select your preferred location.
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
                                        <span>{field}</span>
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
                                disabled={loading} // Disable select while loading
                            >
                                <option value="">All Locations</option>
                                <option value="Morocco">Morocco</option>
                                <option value="France">France</option>
                            </select>
                        </div>

                        <div className="button-group">
                            <button
                                onClick={() => setStep(1)}
                                className="btn btn-secondary"
                                disabled={loading} // Disable back button while loading
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
                                Start Over
                            </button>
                        </div>

                        {loading ? ( // Show spinner while loading jobs
                            <div className="loading-jobs">
                                {renderSpinner()}
                                <p>Loading job results...</p>
                            </div>
                        ) : jobs.length === 0 ? (
                            <p>
                                No internships found for "{selectedField}" in "
                                {location || 'All Locations'}". Try a different
                                field or location.
                            </p>
                        ) : (
                            <div className="job-list">
                                {jobs.map((job, idx) => (
                                    <div key={idx} className="job-card">
                                        <h3>{job.title}</h3>
                                        <p className="company">{job.company}</p>
                                        <p className="location">
                                            {job.location ||
                                                'Location not specified'}{' '}
                                            • {job.source}
                                        </p>
                                        <a
                                            href={job.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="job-link"
                                        >
                                            View Job →
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
