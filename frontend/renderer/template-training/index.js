import React from 'react';
import { createRoot } from 'react-dom/client';
import TemplateTraining from '../components/template-training/TemplateTraining';

const container = document.getElementById('template-training-root');
const root = createRoot(container);
root.render(<TemplateTraining />); 