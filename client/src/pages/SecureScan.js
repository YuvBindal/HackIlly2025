import React, { useState, useRef, useEffect } from 'react';
import { FaSearch, FaGithub, FaShieldAlt, FaFolder, FaFolderOpen, FaFile, FaFileCode, FaFileAlt, FaFileArchive, FaFileImage, FaProjectDiagram, FaCode } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import FolderTree from 'react-folder-tree';
import RepoTreeGraph from '../components/RepoTreeGraph';
import './SecureScan.css';

// Custom theme for the folder tree
const treeTheme = {
  text: {
    color: '#fff',
    fontSize: '14px',
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
  },
  node: {
    backgroundColor: 'transparent',
  },
  arrow: {
    color: 'var(--solana-teal)',
    size: '16px',
  },
  folder: {
    color: 'var(--solana-purple)',
  },
  file: {
    color: 'var(--solana-blue)',
  },
};

// Custom icons for different file types
const getFileIcon = (fileName) => {
  const extension = fileName.split('.').pop().toLowerCase();
  
  switch (extension) {
    case 'rs':
    case 'js':
    case 'ts':
    case 'py':
    case 'jsx':
    case 'tsx':
    case 'c':
    case 'cpp':
    case 'h':
      return <FaFileCode className="file-icon code-file" />;
    case 'md':
    case 'txt':
    case 'log':
    case 'toml':
      return <FaFileAlt className="file-icon doc-file" />;
    case 'zip':
    case 'tar':
    case 'gz':
    case 'rar':
    case 'lock':
      return <FaFileArchive className="file-icon archive-file" />;
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
      return <FaFileImage className="file-icon image-file" />;
    default:
      return <FaFile className="file-icon" />;
  }
};

// Custom renderer for tree nodes
const customNodeRenderer = (props) => {
  const { node, onToggle } = props;
  const { name, isOpen, isFile, fileDescription } = node;
  
  // Add a file extension class for styling
  const fileExtension = isFile ? name.split('.').pop().toLowerCase() : '';
  const fileTypeClass = isFile ? `file-type-${fileExtension}` : '';
  
  return (
    <div 
      className={`rft-tree-item ${props.selected ? 'selected' : ''} ${fileTypeClass}`} 
      onClick={onToggle}
      title={isFile ? name : `${name} (folder)`}
    >
      {isFile ? (
        <>
          {getFileIcon(name)}
          <span 
            className="rft-tree-item-text"
            data-description={fileDescription || "No description available"}
          >
            {name}
          </span>
        </>
      ) : (
        <>
          {isOpen ? 
            <FaFolderOpen className="folder-icon folder-open" /> : 
            <FaFolder className="folder-icon" />
          }
          <span className="rft-tree-item-text">{name}</span>
        </>
      )}
    </div>
  );
};

const SecureScan = () => {
  // State management
  const [programId, setProgramId] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [securityScanResult, setSecurityScanResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [currentStreamingLine, setCurrentStreamingLine] = useState(0);
  const [displayedCode, setDisplayedCode] = useState([]);
  const [treeData, setTreeData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [viewMode, setViewMode] = useState('folder-tree'); // 'folder-tree', 'd3-tree', or 'json'
  const [repoStructure, setRepoStructure] = useState(null);
  
  // Refs
  const codeContainerRef = useRef(null);

  // Form handlers
  const handleProgramIdChange = (e) => setProgramId(e.target.value);

  // Handle node selection in the folder tree
  const handleNodeSelect = (node) => {
    setSelectedNode(node);
  };

  // Convert flat JSON structure to tree format for react-folder-tree
  const convertToTreeFormat = (jsonStructure) => {
    try {
      // Parse the JSON string if it's a string
      const structure = typeof jsonStructure === 'string' ? JSON.parse(jsonStructure) : jsonStructure;
      
      // Convert the structure to the format expected by react-folder-tree
      const convertStructure = (obj, name = 'root') => {
        // If it's a string (file description), return a file node
        if (typeof obj === 'string') {
          return {
            name,
            isOpen: true,
            isFile: true,
            fileDescription: obj || `File: ${name}`,
          };
        }
        
        // If it's an object (directory), process its children
        const children = Object.entries(obj).map(([key, value]) => convertStructure(value, key));
        
        return {
          name,
          isOpen: true,
          children,
        };
      };
      
      return convertStructure(structure);
    } catch (error) {
      console.error('Error converting repository structure:', error);
      return {
        name: 'Error',
        isOpen: true,
        children: [
          {
            name: 'Failed to parse repository structure',
            isFile: true,
          },
        ],
      };
    }
  };

  const handleValidateProgram = async () => {
    if (!programId) return;
    
    setIsValidating(true);
    setValidationResult(null);
    setSecurityScanResult(null); // Reset scan results when validating a new program
    setTreeData(null);
    setRepoStructure(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/validate-program', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ programId }),
      });
      
      const data = await response.json();
      console.log("API Response:", data);
      setValidationResult(data);
      
      // Process repository structure if available
      if (data.validated && data.RepoStructure) {
        let parsedRepoStructure;
        
        // Parse the repository structure if it's a string
        try {
          // First, try to parse as JSON if it's a string
          parsedRepoStructure = typeof data.RepoStructure === 'string' 
            ? JSON.parse(data.RepoStructure) 
            : data.RepoStructure;
          
          console.log("Parsed repository structure:", parsedRepoStructure);
          
          // Check if the structure is flat (all files at root level)
          // If so, try to organize them into folders
          if (typeof parsedRepoStructure === 'object' && !Array.isArray(parsedRepoStructure)) {
            const hasNestedStructure = Object.values(parsedRepoStructure).some(
              value => typeof value === 'object' && value !== null
            );
            
            if (!hasNestedStructure) {
              console.log("Flat structure detected, organizing into folders");
              
              // Create a more structured format by grouping files
              const organizedStructure = {};
              
              // Group files by directory or type
              Object.keys(parsedRepoStructure).forEach(fileName => {
                const description = parsedRepoStructure[fileName];
                
                // Check if the file has a path structure (contains slashes)
                if (fileName.includes('/')) {
                  // Extract the directory path
                  const lastSlashIndex = fileName.lastIndexOf('/');
                  const dirPath = fileName.substring(0, lastSlashIndex);
                  const baseName = fileName.substring(lastSlashIndex + 1);
                  
                  // Create nested structure
                  let current = organizedStructure;
                  const dirs = dirPath.split('/');
                  
                  dirs.forEach(dir => {
                    if (!current[dir]) {
                      current[dir] = {};
                    }
                    current = current[dir];
                  });
                  
                  // Add the file to the deepest directory
                  current[baseName] = description;
                } else {
                  // Files at root level - group by extension
                  const extension = fileName.split('.').pop().toLowerCase();
                  let category;
                  
                  if (['rs'].includes(extension)) {
                    category = 'src';
                  } else if (['js', 'jsx', 'ts', 'tsx'].includes(extension)) {
                    category = 'js';
                  } else if (['toml', 'json'].includes(extension)) {
                    category = 'config';
                  } else if (['lock'].includes(extension)) {
                    category = 'dependencies';
                  } else if (['md', 'txt'].includes(extension)) {
                    category = 'docs';
                  } else {
                    category = 'other';
                  }
                  
                  if (!organizedStructure[category]) {
                    organizedStructure[category] = {};
                  }
                  
                  organizedStructure[category][fileName] = description;
                }
              });
              
              // Use the organized structure instead
              parsedRepoStructure = organizedStructure;
              console.log("Organized structure:", parsedRepoStructure);
            }
          }
          
          // Store the original repo structure for the D3 visualization
          setRepoStructure(parsedRepoStructure);
          
          // Convert to tree format for the folder tree component
          const treeFormatData = convertToTreeFormat(parsedRepoStructure);
          console.log("Converted tree format:", treeFormatData);
          setTreeData(treeFormatData);
        } catch (parseError) {
          console.error("Error parsing repository structure:", parseError);
          setRepoStructure(data.RepoStructure); // Use the original data as fallback
          setTreeData(convertToTreeFormat(data.RepoStructure));
        }
      }
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
    setTreeData(null);
    setRepoStructure(null);
  };

  // Custom renderer for tree nodes with selection handling
  const customNodeRendererWithSelection = (props) => {
    const { node, onToggle } = props;
    const { name, isOpen, isFile, fileDescription } = node;
    
    // Add a file extension class for styling
    const fileExtension = isFile ? name.split('.').pop().toLowerCase() : '';
    const fileTypeClass = isFile ? `file-type-${fileExtension}` : '';
    
    // Check if this node is selected
    const isSelected = selectedNode && selectedNode.name === name && 
                      selectedNode.fileDescription === fileDescription;
    
    return (
      <div 
        className={`rft-tree-item ${isSelected ? 'selected' : ''} ${fileTypeClass}`} 
        onClick={(e) => {
          onToggle(e);
          handleNodeSelect(node);
        }}
        title={isFile ? name : `${name} (folder)`}
      >
        {isFile ? (
          <>
            {getFileIcon(name)}
            <span 
              className="rft-tree-item-text"
              data-description={fileDescription || "No description available"}
            >
              {name}
            </span>
          </>
        ) : (
          <>
            {isOpen ? 
              <FaFolderOpen className="folder-icon folder-open" /> : 
              <FaFolder className="folder-icon" />
            }
            <span className="rft-tree-item-text">{name}</span>
          </>
        )}
      </div>
    );
  };

  // Update the useEffect that processes the validation result
  useEffect(() => {
    if (validationResult && validationResult.RepoStructure) {
      try {
        // Parse the repository structure if it's a string
        const repoStructureData = typeof validationResult.RepoStructure === 'string' 
          ? JSON.parse(validationResult.RepoStructure) 
          : validationResult.RepoStructure;
        
        console.log("Original repo structure:", repoStructureData);
        
        // Store the original repo structure for the D3 visualization
        setRepoStructure(repoStructureData);
        
        // Convert to tree format for the folder tree component
        const treeFormatted = convertToTreeFormat(repoStructureData);
        setTreeData(treeFormatted);
      } catch (error) {
        console.error("Error parsing repository structure:", error);
        setTreeData(null);
        setRepoStructure(null);
      }
    } else {
      setTreeData(null);
      setRepoStructure(null);
    }
  }, [validationResult]);

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
            <p>Validating program ID using osec.io...</p>
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
            {validationResult.validated && treeData && (
              <div className="repo-structure">
                <h4>Repository Structure 
                  {validationResult.repoUrl && (
                    <a href={validationResult.repoUrl} target="_blank" rel="noopener noreferrer" className="repo-link">
                      <FaGithub /> View on GitHub
                    </a>
                  )}
                </h4>
                
                {/* View mode toggle buttons */}
                <div className="view-mode-toggle">
                  <button 
                    className={`view-mode-btn ${viewMode === 'folder-tree' ? 'active' : ''}`}
                    onClick={() => setViewMode('folder-tree')}
                  >
                    <FaFolderOpen /> Folder Tree
                  </button>
                  <button 
                    className={`view-mode-btn ${viewMode === 'd3-tree' ? 'active' : ''}`}
                    onClick={() => setViewMode('d3-tree')}
                  >
                    <FaProjectDiagram /> D3 Tree
                  </button>
                  <button 
                    className={`view-mode-btn ${viewMode === 'json' ? 'active' : ''}`}
                    onClick={() => setViewMode('json')}
                  >
                    <FaCode /> JSON
                  </button>
                </div>
                
                {treeData ? (
                  <>
                    {viewMode === 'folder-tree' && (
                      <div className="folder-tree-container">
                        <FolderTree
                          data={treeData}
                          showCheckbox={false}
                          readOnly
                          indentPixels={20}
                          renderNode={customNodeRendererWithSelection}
                          onNameClick={(node) => handleNodeSelect(node)}
                        />
                        {selectedNode && (
                          <div className="selected-file-info">
                            <h5>{selectedNode.name}</h5>
                            <p>{selectedNode.fileDescription || `No additional information available for ${selectedNode.name}`}</p>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {viewMode === 'd3-tree' && (
                      <RepoTreeGraph 
                        repoStructure={repoStructure} 
                        repoUrl={validationResult.repoUrl}
                      />
                    )}
                    
                    {viewMode === 'json' && (
                      <pre className="json-view">{JSON.stringify(treeData, null, 2)}</pre>
                    )}
                  </>
                ) : (
                  <p>No repository structure available.</p>
                )}
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
                  <ReactMarkdown>{securityScanResult.Report}</ReactMarkdown>
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