import CoordinatePreviewButton from '../components/preview/components/CoordinatePreviewButton';
import { FaMouse, FaKeyboard, FaFile, FaPlus, FaEdit, FaArrowRight, FaUndo, FaTerminal, FaCode, FaCube } from 'react-icons/fa';

// Helper function to get filename from path
const getFileName = (filepath) => {
  return filepath.split('/').pop().split('\\').pop();
};

export const FILE_EDIT_TOOLS_NAME = ['bash_run', 'str_replace_editor', 'view', 'create', 'str_replace', 'insert', 'undo_edit'];

export const TOOL_ACTION_MAPPING = {
  // Bash script execution
  bash_run: {
    label: (tool) => <><FaTerminal /> Execute Script</>,
    description: (tool) => {
      if (!tool.input) return 'Run bash script';
      return {
        text: 'Run bash script',
        component: (
          <>
            <hr style={{ margin: '8px 0', borderColor: '#444' }} />
            <div style={{ fontFamily: 'monospace' }}>
              <strong>Runtime:</strong> {tool.input.runtime}
              <br />
              <strong>Script:</strong> {tool.input.script}
            </div>
          </>
        )
      };
    }
  },
  view: {
    label: 'View File',
    description: (tool) => {
      if (!tool.input) return 'View file contents';
      return {
        text: 'View file contents',
        component: (
          <div style={{ fontFamily: 'monospace' }}>
            <strong>Path:</strong> {tool.input.path}
          </div>
        )
      };
    }
  },
  create: {
    label: 'Create File',
    description: (tool) => {
      if (!tool.input) return 'Create new file';
      return {
        text: 'Create new file',
        component: (
          <div style={{ fontFamily: 'monospace' }}>
            <strong>Path:</strong> {tool.input.path}
            {/* <br />
            <strong>Content:</strong>
            <pre>{tool.input.content}</pre> */}
          </div>
        )
      };
    }
  },
  str_replace: {
    label: 'Edit File',
    description: (tool) => {
      if (!tool.input) return 'Replace text in file';
      return {
        text: 'Replace text in file',
        component: (
          <div style={{ fontFamily: 'monospace' }}>
            <strong>Path:</strong> {tool.input.path}
            <br />
            <strong>Replace:</strong> "{tool.input.old_str}"
            <br />
            <strong>With:</strong> "{tool.input.new_str}"
          </div>
        )
      };
    }
  },
  insert: {
    label: 'Insert Text',
    description: (tool) => {
      if (!tool.input) return 'Insert text at specific line';
      return {
        text: 'Insert text at specific line',
        component: (
          <div style={{ fontFamily: 'monospace' }}>
            <strong>Path:</strong> {tool.input.path}
            <br />
            <strong>At line:</strong> {tool.input.insert_line}
            {/* <br />
            <strong>Content:</strong>
            <pre>{tool.input.new_str}</pre> */}
          </div>
        )
      };
    }
  },

  // Screenshot
  screenshot: {
    label: 'Taking Screenshot',
    description: () => 'Capturing screen content'
  },

  // Mouse clicks
  left_click: {
    label: () => <><FaMouse /> left click</>,
    description: (tool) => tool.input?.coordinate ? 
      `Click at coordinates (${tool.input.coordinate[0]}, ${tool.input.coordinate[1]})` : 
      'Left mouse click'
  },
  right_click: {
    label: () => <><FaMouse /> right click</>,
    description: (tool) => tool.input?.coordinate ? 
      `Right click at coordinates (${tool.input.coordinate[0]}, ${tool.input.coordinate[1]})` : 
      'Right mouse click'
  },
  middle_click: {
    label: () => <><FaMouse /> middle click</>,
    description: (tool) => tool.input?.coordinate ? 
      `Middle click at coordinates (${tool.input.coordinate[0]}, ${tool.input.coordinate[1]})` : 
      'Middle mouse click'
  },
  double_click: {
    label: () => <><FaMouse /> double click</>,
    description: (tool) => tool.input?.coordinate ? 
      `Double click at coordinates (${tool.input.coordinate[0]}, ${tool.input.coordinate[1]})` : 
      'Double mouse click'
  },

  // Keyboard inputs
  type: {
    label: (tool) => {
      const text = tool.input?.text || '';
      const firstThreeWords = text.split(' ').slice(0, 3).join(' ');
      return <><FaKeyboard /> typing {firstThreeWords}</>;
    },
    description: (tool) => ({
      text: 'Typing text',
      component: tool.input?.text ? (
        <div style={{ fontFamily: 'monospace' }}>
          <strong>Text:</strong> {tool.input.text}
        </div>
      ) : null
    })
  },
  key: {
    label: (tool) => <><FaKeyboard /> {tool.input?.text || ''}</>,
    description: (tool) => tool.input?.text ? `Pressing key: ${tool.input.text}` : 'Pressing key'
  },

  // Mouse movement
  mouse_move: {
    label: (tool) => {
      if (!tool.input?.coordinate) return <><FaMouse /> move</>;
      const [x, y] = tool.input.coordinate;
      return (
        <>
          <FaMouse /> move <CoordinatePreviewButton x={x} y={y} />
        </>
      );
    },
    description: (tool) => tool.input?.coordinate ? 
      `Moving mouse to coordinates (${tool.input.coordinate[0]}, ${tool.input.coordinate[1]})` : 
      'Moving mouse'
  },

  str_replace_editor: {
    label: (tool) => {
      const fileName = getFileName(tool.input.path);
      const commandLabels = {
        'view': () => <><FaFile /> view <span className="file-link">{fileName}</span></>,
        'create': () => <><FaPlus /> create <span className="file-link">{fileName}</span></>,
        'str_replace': () => <><FaEdit /> edit <span className="file-link">{fileName}</span></>,
        'insert': () => <><FaArrowRight /> insert into <span className="file-link">{fileName}</span></>,
        'undo_edit': () => <><FaUndo /> undo changes to <span className="file-link">{fileName}</span></>,
      };
      return commandLabels[tool.input.command]?.() || 'File Operation';
    },
    description: (tool) => {
      if (!tool.input) return 'File operation';
      
      const descriptions = {
        'view': {
          text: 'View file contents',
          component: <div style={{ fontFamily: 'monospace' }}><strong>Path:</strong> {tool.input.path}</div>
        },
        'create': {
          text: 'Create new file',
          component: (
            <div style={{ fontFamily: 'monospace' }}>
              <strong>Path:</strong> {tool.input.path}
              {/* <br />
              <strong>Content:</strong>
              <pre>{tool.input.file_text}</pre> */}
            </div>
          )
        },
        'str_replace': {
          text: 'Replace text in file',
          component: (
            <div style={{ fontFamily: 'monospace' }}>
              <strong>Path:</strong> {tool.input.path}
              <br />
              <strong>Replace:</strong> "{tool.input.old_str}"
              <br />
              <strong>With:</strong> "{tool.input.new_str}"
            </div>
          )
        },
        'insert': {
          text: 'Insert text at line',
          component: (
            <div style={{ fontFamily: 'monospace' }}>
              <strong>Path:</strong> {tool.input.path}
              <br />
              <strong>At line:</strong> {tool.input.insert_line}
              {/* <br />
              <strong>Content:</strong>
              <pre>{tool.input.new_str}</pre> */}
            </div>
          )
        },
        'undo_edit': {
          text: 'Undo changes',
          component: (
            <div style={{ fontFamily: 'monospace' }}>
              <strong>Path:</strong> {tool.input.path}
            </div>
          )
        }
      };
      return descriptions[tool.input.command] || { text: 'File operation' };
    }
  },

  paraview: {
    label: (tool) => <><FaCube /> ParaView Script</>,
    description: (tool) => {
      if (!tool.input) return 'Execute ParaView visualization script';
      return {
        text: 'Execute ParaView visualization script',
        component: (
          <div style={{ fontFamily: 'monospace' }}>
            <strong>Script:</strong>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '8px',
              borderRadius: '4px',
              marginTop: '4px'
            }}>
              {tool.input.script}
            </pre>
          </div>
        )
      };
    }
  }
}; 