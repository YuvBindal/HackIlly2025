import React, { useState, useEffect, useRef } from 'react';
import Tree from 'react-d3-tree';
import { FaFolder, FaFolderOpen, FaFile, FaFileCode, FaFileAlt, FaFileArchive, FaFileImage } from 'react-icons/fa';
import './RepoTreeGraph.css';

// Custom node renderer for the D3 tree
const CustomNodeElement = ({ nodeDatum, toggleNode, onNodeClick }) => {
  const isFolder = nodeDatum.children && nodeDatum.children.length > 0;
  const isRoot = nodeDatum.name === 'Repository Root';
  const depth = nodeDatum.__rd3t.depth || 0;
  
  // Determine file type for styling
  let nodeClass = isFolder ? 'folder-node' : 'file-node';
  let fileType = '';
  
  if (!isFolder && nodeDatum.name) {
    const extension = nodeDatum.name.split('.').pop().toLowerCase();
    
    if (['js', 'jsx', 'ts', 'tsx', 'py', 'rs', 'go', 'java', 'c', 'cpp', 'h', 'php', 'rb'].includes(extension)) {
      fileType = 'code-file';
    } else if (['md', 'txt', 'log', 'toml', 'yaml', 'yml', 'json', 'html', 'css'].includes(extension)) {
      fileType = 'doc-file';
    } else if (['zip', 'tar', 'gz', 'rar', 'lock'].includes(extension)) {
      fileType = 'archive-file';
    } else if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico'].includes(extension)) {
      fileType = 'image-file';
    }
  }
  
  // Get appropriate icon
  const getIcon = () => {
    if (isFolder) {
      return nodeDatum.__rd3t.collapsed ? <FaFolder /> : <FaFolderOpen />;
    }
    
    if (fileType === 'code-file') return <FaFileCode />;
    if (fileType === 'doc-file') return <FaFileAlt />;
    if (fileType === 'archive-file') return <FaFileArchive />;
    if (fileType === 'image-file') return <FaFileImage />;
    
    return <FaFile />;
  };
  
  // Calculate width based on node depth for better visualization
  const nodeWidth = Math.max(180, 220 - depth * 10);
  
  return (
    <g onClick={(evt) => {
      evt.stopPropagation();
      if (isFolder) toggleNode();
      onNodeClick(nodeDatum);
    }}>
      <foreignObject width={nodeWidth} height={40} x={-nodeWidth/2} y={-20}>
        <div 
          className={`tree-node ${nodeClass} ${fileType} ${isRoot ? 'root-node' : ''}`}
          data-description={nodeDatum.description || `${nodeDatum.name} ${isFolder ? 'folder' : 'file'}`}
          data-depth={depth}
        >
          <span className="node-icon">{getIcon()}</span>
          <span className="node-label">{nodeDatum.name}</span>
        </div>
      </foreignObject>
    </g>
  );
};

// Convert the repository structure to D3 tree format
const convertToD3TreeFormat = (repoStructure) => {
  if (!repoStructure) return null;
  
  console.log("Converting to D3 tree format, raw data:", repoStructure);
  
  // Create a root node
  const rootNode = {
    name: 'Repository Root',
    children: []
  };
  
  // Handle different data formats
  try {
    // If it's already in the expected format for D3 tree
    if (repoStructure.name && Array.isArray(repoStructure.children)) {
      console.log("Data is already in D3 tree format");
      return repoStructure;
    }
    
    // If it's a string, try to parse it as JSON
    if (typeof repoStructure === 'string') {
      try {
        repoStructure = JSON.parse(repoStructure);
        console.log("Parsed string data:", repoStructure);
      } catch (e) {
        console.error("Failed to parse string data:", e);
      }
    }
    
    // Check if it's the folder tree format from react-folder-tree
    if (repoStructure.isFile !== undefined || (repoStructure.children && Array.isArray(repoStructure.children))) {
      console.log("Converting from folder tree format");
      // Convert from folder tree format
      const convertFromFolderTree = (node) => {
        const result = {
          name: node.name,
          description: node.fileDescription || `${node.name} ${node.isFile ? 'file' : 'folder'}`
        };
        
        if (!node.isFile && node.children && node.children.length > 0) {
          result.children = node.children.map(child => convertFromFolderTree(child));
        }
        
        return result;
      };
      
      return {
        name: 'Repository Root',
        children: repoStructure.children ? repoStructure.children.map(child => convertFromFolderTree(child)) : []
      };
    }
    
    // Special case: Check if it's a flat structure with src/lib/file.rs format
    // This is common in Rust projects
    if (typeof repoStructure === 'object' && !Array.isArray(repoStructure)) {
      console.log("Processing object with keys:", Object.keys(repoStructure));
      
      // Check if keys look like file paths
      const hasFilePaths = Object.keys(repoStructure).some(key => key.includes('/') || key.includes('\\'));
      
      if (hasFilePaths) {
        console.log("Object has file paths as keys");
        
        // Process each file path to build a nested structure
        Object.keys(repoStructure).forEach(filePath => {
          console.log("Processing file path:", filePath);
          
          if (typeof repoStructure[filePath] === 'string') {
            // Split the path into parts (folders and filename)
            const pathParts = filePath.split(/[\/\\]/).filter(part => part.trim() !== '');
            console.log("Path parts:", pathParts);
            
            // Start at the root level
            let currentLevel = rootNode.children;
            let currentPath = '';
            
            // Process each part of the path
            for (let i = 0; i < pathParts.length; i++) {
              const part = pathParts[i];
              currentPath = currentPath ? `${currentPath}/${part}` : part;
              
              // If this is the last part (file)
              if (i === pathParts.length - 1) {
                // Add the file to the current level
                currentLevel.push({
                  name: part,
                  description: repoStructure[filePath] || `File: ${part}`,
                  fullPath: currentPath
                });
              } else {
                // This is a folder, check if it already exists at this level
                let folderNode = currentLevel.find(node => node.name === part);
                
                if (!folderNode) {
                  // Create a new folder node
                  folderNode = {
                    name: part,
                    description: `Folder: ${part}`,
                    fullPath: currentPath,
                    children: []
                  };
                  currentLevel.push(folderNode);
                } else if (!folderNode.children) {
                  // Ensure the folder has a children array
                  folderNode.children = [];
                }
                
                // Move to the next level (inside this folder)
                currentLevel = folderNode.children;
              }
            }
          }
        });
        
        console.log("Converted tree structure:", JSON.stringify(rootNode, null, 2));
        return rootNode;
      }
    }
    
    // If we have a simple object with files at the root level
    if (typeof repoStructure === 'object' && !Array.isArray(repoStructure)) {
      console.log("Processing simple object with files at root level");
      
      // Group files by directory based on naming patterns
      const filesByDir = {};
      
      Object.keys(repoStructure).forEach(fileName => {
        // Check if the file belongs to a common directory pattern
        let dirName = null;
        
        // Check for common directory patterns in filenames
        if (fileName.startsWith('src/')) {
          dirName = 'src';
        } else if (fileName.startsWith('lib/')) {
          dirName = 'lib';
        } else if (fileName.startsWith('tests/')) {
          dirName = 'tests';
        } else if (fileName.endsWith('.rs')) {
          dirName = 'rust';
        } else if (fileName.endsWith('.js') || fileName.endsWith('.jsx') || fileName.endsWith('.ts') || fileName.endsWith('.tsx')) {
          dirName = 'javascript';
        } else if (fileName.endsWith('.toml')) {
          dirName = 'config';
        } else if (fileName.endsWith('.lock')) {
          dirName = 'dependencies';
        } else if (fileName.endsWith('.md')) {
          dirName = 'docs';
        } else if (fileName.endsWith('.json')) {
          dirName = 'config';
        } else {
          dirName = 'other';
        }
        
        if (!filesByDir[dirName]) {
          filesByDir[dirName] = [];
        }
        
        filesByDir[dirName].push({
          name: fileName,
          description: repoStructure[fileName] || `File: ${fileName}`
        });
      });
      
      // Create folder nodes for each directory
      Object.keys(filesByDir).forEach(dirName => {
        const folderNode = {
          name: dirName,
          description: `Folder: ${dirName}`,
          children: filesByDir[dirName]
        };
        
        rootNode.children.push(folderNode);
      });
      
      // If we only have one folder and it's "other", just use the files directly
      if (rootNode.children.length === 1 && rootNode.children[0].name === 'other') {
        rootNode.children = rootNode.children[0].children;
      }
      
      console.log("Grouped files by directory:", rootNode);
      return rootNode;
    }
    
    // If it's an array, try to convert each item
    if (Array.isArray(repoStructure)) {
      console.log("Processing array data");
      
      // First, check if this is an array of file paths
      if (repoStructure.every(item => typeof item === 'string')) {
        console.log("Array of file paths");
        
        // Process each file path to build a tree structure
        repoStructure.forEach(filePath => {
          const pathParts = filePath.split(/[\/\\]/).filter(part => part.trim() !== '');
          let currentLevel = rootNode.children;
          let currentPath = '';
          
          for (let i = 0; i < pathParts.length; i++) {
            const part = pathParts[i];
            currentPath = currentPath ? `${currentPath}/${part}` : part;
            
            if (i === pathParts.length - 1) {
              // This is a file
              currentLevel.push({
                name: part,
                description: `File: ${part}`,
                fullPath: currentPath
              });
            } else {
              // This is a folder
              let folderNode = currentLevel.find(node => node.name === part);
              
              if (!folderNode) {
                folderNode = {
                  name: part,
                  description: `Folder: ${part}`,
                  fullPath: currentPath,
                  children: []
                };
                currentLevel.push(folderNode);
              } else if (!folderNode.children) {
                folderNode.children = [];
              }
              
              currentLevel = folderNode.children;
            }
          }
        });
      } else {
        // It's an array of objects, convert each one
        console.log("Array of objects");
        
        rootNode.children = repoStructure.map(item => {
          if (typeof item === 'string') {
            return { name: item };
          } else if (typeof item === 'object') {
            const node = { 
              name: item.name || 'Unknown',
              description: item.description || item.fileDescription || 'No description'
            };
            
            if (item.children && Array.isArray(item.children)) {
              node.children = item.children.map(child => {
                if (typeof child === 'string') {
                  return { name: child };
                }
                return { 
                  name: child.name || 'Unknown',
                  description: child.description || child.fileDescription || 'No description',
                  children: child.children ? child.children.map(c => ({ name: c.name || 'Unknown' })) : undefined
                };
              });
            }
            
            return node;
          }
          return { name: 'Unknown' };
        });
      }
      
      console.log("Processed array data:", rootNode);
      return rootNode;
    }
    
    // Fallback: create a simple structure based on file extensions
    console.log("Using fallback method to create structure");
    
    // Create a simple structure with files grouped by type
    const filesByType = {
      'Rust Files': [],
      'JavaScript Files': [],
      'Configuration Files': [],
      'Documentation': [],
      'Other Files': []
    };
    
    // Try to extract files from the structure
    const extractFiles = (obj) => {
      if (typeof obj === 'object' && obj !== null) {
        Object.keys(obj).forEach(key => {
          const value = obj[key];
          
          // If the value is a string, treat the key as a filename
          if (typeof value === 'string') {
            const extension = key.split('.').pop().toLowerCase();
            
            if (['rs'].includes(extension)) {
              filesByType['Rust Files'].push({ name: key, description: value });
            } else if (['js', 'jsx', 'ts', 'tsx'].includes(extension)) {
              filesByType['JavaScript Files'].push({ name: key, description: value });
            } else if (['toml', 'json', 'lock'].includes(extension)) {
              filesByType['Configuration Files'].push({ name: key, description: value });
            } else if (['md', 'txt'].includes(extension)) {
              filesByType['Documentation'].push({ name: key, description: value });
            } else {
              filesByType['Other Files'].push({ name: key, description: value });
            }
          } else if (typeof value === 'object' && value !== null) {
            extractFiles(value);
          }
        });
      }
    };
    
    extractFiles(repoStructure);
    
    // Add non-empty file type folders to the root
    Object.keys(filesByType).forEach(type => {
      if (filesByType[type].length > 0) {
        rootNode.children.push({
          name: type,
          description: `Folder: ${type}`,
          children: filesByType[type]
        });
      }
    });
    
    console.log("Created fallback structure:", rootNode);
    return rootNode;
  } catch (error) {
    console.error("Error converting to D3 tree format:", error);
    return {
      name: 'Error',
      children: [{ name: 'Error processing data', description: error.message }]
    };
  }
};

const RepoTreeGraph = ({ repoStructure, repoUrl }) => {
  const [treeData, setTreeData] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  
  // Convert repository structure to D3 tree format
  useEffect(() => {
    if (repoStructure) {
      try {
        console.log("Converting repository structure:", repoStructure);
        
        // If the structure is a string, try to parse it
        let processedStructure = repoStructure;
        if (typeof repoStructure === 'string') {
          try {
            processedStructure = JSON.parse(repoStructure);
          } catch (e) {
            console.error("Failed to parse repository structure string:", e);
          }
        }
        
        // Check if we need to create a nested structure
        if (typeof processedStructure === 'object' && !Array.isArray(processedStructure)) {
          const hasNestedStructure = Object.values(processedStructure).some(
            value => typeof value === 'object' && value !== null && !Array.isArray(value)
          );
          
          if (!hasNestedStructure) {
            // Create a more structured format for flat objects
            const organizedStructure = {};
            
            // Group files by directory or type
            Object.keys(processedStructure).forEach(fileName => {
              const description = processedStructure[fileName];
              
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
                // Group files by extension
                const extension = fileName.split('.').pop().toLowerCase();
                let category;
                
                if (['rs'].includes(extension)) {
                  category = 'src';
                } else if (['js', 'jsx', 'ts', 'tsx'].includes(extension)) {
                  category = 'js';
                } else if (['toml'].includes(extension)) {
                  category = 'config';
                } else if (['lock'].includes(extension)) {
                  category = 'dependencies';
                } else if (['md'].includes(extension)) {
                  category = 'docs';
                } else if (['json'].includes(extension)) {
                  category = 'config';
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
            processedStructure = organizedStructure;
            console.log("Organized structure for D3 tree:", processedStructure);
          }
        }
        
        const d3TreeData = convertToD3TreeFormat(processedStructure);
        console.log("Converted D3 tree data:", d3TreeData);
        setTreeData(d3TreeData);
        setError(null);
      } catch (err) {
        console.error("Error processing repository structure:", err);
        setError("Failed to process repository structure: " + err.message);
      }
    }
  }, [repoStructure]);
  
  // Update dimensions when the component mounts or window resizes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);
  
  // Handle node click
  const handleNodeClick = (nodeDatum) => {
    setSelectedNode(nodeDatum);
  };
  
  return (
    <div className="repo-tree-graph-container" ref={containerRef}>
      {error ? (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Retry</button>
        </div>
      ) : treeData ? (
        <>
          <Tree
            data={treeData}
            orientation="horizontal"
            pathFunc="step"
            translate={{ x: dimensions.width / 8, y: dimensions.height / 2 }}
            renderCustomNodeElement={(rd3tProps) => 
              CustomNodeElement({ ...rd3tProps, onNodeClick: handleNodeClick })
            }
            separation={{ siblings: 1.5, nonSiblings: 2 }}
            zoomable={true}
            collapsible={true}
            nodeSize={{ x: 300, y: 50 }}
            enableLegacyTransitions={true}
            transitionDuration={800}
            initialDepth={1}
            scaleExtent={{ min: 0.3, max: 1.2 }}
            zoom={0.7}
            onNodeClick={(nodeDatum, evt) => {
              if (nodeDatum.children && nodeDatum.children.length > 0) {
                // Toggle node expansion
                nodeDatum.__rd3t.collapsed = !nodeDatum.__rd3t.collapsed;
              }
              handleNodeClick(nodeDatum);
            }}
          />
          
          {selectedNode && (
            <div className="selected-file-info">
              <h5>{selectedNode.name}</h5>
              <p>{selectedNode.description || `No additional information available for ${selectedNode.name}`}</p>
            </div>
          )}
        </>
      ) : (
        <div className="loading-tree">
          Loading repository structure...
        </div>
      )}
    </div>
  );
};

export default RepoTreeGraph; 