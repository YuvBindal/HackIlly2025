import React, { useState, useRef, useEffect } from 'react';
import { FaSearch, FaGithub, FaShieldAlt } from 'react-icons/fa';
import './SecureScan.css';

const SecureScan = () => {
  // State management
  const [programId, setProgramId] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [securityScanResult, setSecurityScanResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [currentStreamingLine, setCurrentStreamingLine] = useState(0);
  const [displayedCode, setDisplayedCode] = useState([]);
  
  // Refs
  const codeContainerRef = useRef(null);

  // Form handlers
  const handleProgramIdChange = (e) => setProgramId(e.target.value);

  const handleValidateProgram = async () => {
    if (!programId) return;
    
    setIsValidating(true);
    setValidationResult(null);
    setSecurityScanResult(null); // Reset scan results when validating a new program
    
    try {
      const response = await fetch('http://localhost:8000/api/validate-program', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ programId }),
      });
      
      const data = await response.json();
      setValidationResult(data);
    } catch (error) {
      console.error('Error validating program:', error);
      setValidationResult({
        status: 'error',
        validated: false,
        message: 'Failed to validate program ID. Please try again.'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSecurityScan = async () => {
    if (!validationResult?.validated || !validationResult?.repoUrl) return;
    
    setIsScanning(true);
    setSecurityScanResult(null);
    setDisplayedCode([]);
    setCurrentStreamingLine(0);
    
    try {
      const response = await fetch('http://localhost:8000/api/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ githubUrl: validationResult.repoUrl }),
      });
      
      const data = await response.json();
      
      // Store the full result
      setSecurityScanResult(data);
      
      // Start the code streaming animation
      if (data.RawCode) {
        const codeLines = data.RawCode.split('\n');
        streamCodeLines(codeLines);
      }
    } catch (error) {
      console.error('Error scanning code:', error);
      setSecurityScanResult({
        status: 'error',
        message: 'Failed to scan repository. Please try again.'
      });
    } finally {
      setIsScanning(false);
    }
  };

  // Function to animate code streaming
  const streamCodeLines = (codeLines) => {
    let currentLine = 0;
    
    const streamInterval = setInterval(() => {
      if (currentLine < codeLines.length) {
        setDisplayedCode(prev => [...prev, codeLines[currentLine]]);
        setCurrentStreamingLine(currentLine + 1);
        currentLine++;
        
        // Auto-scroll to the bottom of the code container
        if (codeContainerRef.current) {
          codeContainerRef.current.scrollTop = codeContainerRef.current.scrollHeight;
        }
      } else {
        clearInterval(streamInterval);
      }
    }, 50); // Adjust speed as needed
  };

  // Reset function to start over
  const handleReset = () => {
    setProgramId('');
    setValidationResult(null);
    setSecurityScanResult(null);
    setDisplayedCode([]);
  };

  // Main component render
  return (
    <div className="secure-scan-container">
      <div className="scan-header">
        <h1>Solana Program Security Scanner</h1>
        <p>Validate and analyze Solana programs for security vulnerabilities</p>
      </div>
      
      {/* Program ID Validation Section */}
      <div className="scan-section program-validation">
        <h2>Validate & Scan Solana Program</h2>
        <div className="input-group">
          <input
            type="text"
            value={programId}
            onChange={handleProgramIdChange}
            placeholder="Enter Solana Program ID"
            disabled={isValidating || validationResult}
          />
          <button 
            className="validate-btn"
            onClick={handleValidateProgram}
            disabled={!programId || isValidating || validationResult}
          >
            <FaSearch /> Validate
          </button>
          {validationResult && (
            <button 
              className="reset-btn"
              onClick={handleReset}
              disabled={isValidating || isScanning}
            >
              Reset
            </button>
          )}
        </div>
        
        {isValidating && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Validating program ID...</p>
          </div>
        )}
        
        {validationResult && (
          <div className={`validation-result ${validationResult.validated ? 'success' : 'error'}`}>
            <h3>
              {validationResult.validated 
                ? 'Program Validated' 
                : validationResult.status === 'success' 
                  ? 'Program Not Validated (as per osec.io)' 
                  : 'Validation Failed'}
            </h3>
            {validationResult.validated && (
              <div className="repo-structure">
                <h4>Repository Structure:</h4>
                <pre>{validationResult.RepoStructure}</pre>
              </div>
            )}
            {!validationResult.validated && validationResult.message && (
              <p className="validation-message">{validationResult.message}</p>
            )}
          </div>
        )}
      </div>

      {/* Security Scan Section - Only shown when program is validated */}
      {validationResult?.validated && (
        <div className="scan-section security-scan">
          <div className="scan-button-container">
            <button 
              className="scan-btn"
              onClick={handleSecurityScan}
              disabled={isScanning}
            >
              <FaShieldAlt /> Scan Code for Vulnerabilities
            </button>
          </div>
          
          {isScanning && (
            <div className="loading-indicator">
              <div className="spinner"></div>
              <p>Scanning repository for vulnerabilities...</p>
            </div>
          )}
          
          {securityScanResult && (
            <div className="scan-results">
              <h3>Security Scan Results</h3>
              
              <div className="code-display">
                <h4>Code Analysis:</h4>
                <div className="code-container" ref={codeContainerRef}>
                  {displayedCode.map((line, index) => {
                    // Find if this line has an annotation
                    const lineAnnotation = securityScanResult.Lines.find(l => l[0] === index+1);
                    const isGoodLine = lineAnnotation && lineAnnotation[2] === 'Good';
                    const isBadLine = lineAnnotation && lineAnnotation[2] === 'Bad';
                    const lineDescription = lineAnnotation ? lineAnnotation[1] : '';
                    
                    return (
                      <pre 
                        key={index} 
                        className={`code-line ${isGoodLine ? 'good-line' : isBadLine ? 'bad-line' : ''}`}
                        title={lineDescription} // Add tooltip with the description
                      >
                        <span className="line-number">{index + 1}</span>
                        <span className="line-content">{line}</span>
                        {(isGoodLine || isBadLine) && (
                          <div className="line-tooltip">
                            <span className={`tooltip-indicator ${isGoodLine ? 'good' : 'bad'}`}>
                              {isGoodLine ? '✓' : '!'} 
                            </span>
                            <span className="tooltip-text">{lineDescription}</span>
                          </div>
                        )}
                      </pre>
                    );
                  })}
                </div>
              </div>
              
              <div className="issues-list">
                <h4>Identified Issues:</h4>
                <ul>
                  {securityScanResult.Lines
                    .filter(line => line[2] === 'Bad')
                    .sort((a, b) => a[0] - b[0]) // Sort by line number (first element in each line array)
                    .map((line, index) => (
                      <li key={index} className="issue-item">
                        <span className="line-ref">Line {line[0]}:</span> {line[1]}
                      </li>
                    ))}
                </ul>
              </div>
              
              <div className="security-report">
                <h4>Security Report:</h4>
                <div className="report-content">
                  {securityScanResult.Report}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SecureScan;