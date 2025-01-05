import CoordinatePreviewButton from '../components/preview/components/CoordinatePreviewButton';

export const TOOL_ACTION_MAPPING = {
  // Command and file operations
  command: {
    label: 'Execute Command',
    description: (tool) => {
      let desc = 'Run system command';
      if (tool.input) {
        desc += '\n\nInputs:';
        Object.entries(tool.input).forEach(([key, value]) => {
          desc += `\n${key}: ${value}`;
        });
      }
      return desc;
    }
  },
  view: {
    label: 'View File',
    description: (tool) => {
      let desc = 'View file contents';
      if (tool.input) {
        desc += '\n\nInputs:';
        Object.entries(tool.input).forEach(([key, value]) => {
          desc += `\n${key}: ${value}`;
        });
      }
      return desc;
    }
  },
  create: {
    label: 'Create File',
    description: (tool) => {
      let desc = 'Create new file';
      if (tool.input) {
        desc += '\n\nInputs:';
        Object.entries(tool.input).forEach(([key, value]) => {
          desc += `\n${key}: ${value}`;
        });
      }
      return desc;
    }
  },
  str_replace: {
    label: 'Edit File',
    description: (tool) => {
      let desc = 'Replace text in file';
      if (tool.input) {
        desc += '\n\nInputs:';
        Object.entries(tool.input).forEach(([key, value]) => {
          desc += `\n${key}: ${value}`;
        });
      }
      return desc;
    }
  },
  insert: {
    label: 'Insert Text',
    description: (tool) => {
      let desc = 'Insert text at specific line';
      if (tool.input) {
        desc += '\n\nInputs:';
        Object.entries(tool.input).forEach(([key, value]) => {
          desc += `\n${key}: ${value}`;
        });
      }
      return desc;
    }
  },

  // Screenshot
  screenshot: {
    label: 'Taking Screenshot',
    description: () => ''
  },

  // Mouse clicks
  left_click: {
    label: 'Left Click',
    description: () => ''
  },
  right_click: {
    label: 'Right Click',
    description: () => ''
  },
  middle_click: {
    label: 'Middle Click',
    description: () => ''
  },
  double_click: {
    label: 'Double Click',
    description: () => ''
  },

  // Keyboard inputs
  type: {
    label: 'Typing...',
    description: (tool) => tool.input?.text || ''
  },
  key: {
    label: (tool) => `Pressing ${tool.input?.text || ''}`,
    description: () => ''
  },

  // Mouse movement
  mouse_move: {
    label: (tool) => {
      if (!tool.input?.coordinate) return 'Move the cursor';
      const [x, y] = tool.input.coordinate;
      return (
        <>
          Move the cursor <CoordinatePreviewButton x={x} y={y} />
        </>
      );
    },
    description: () => ''
  }
}; 