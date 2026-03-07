import React from 'react';
import FormComponent from './components/FormComponent';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>woodVisionAI - フォーム管理</h1>
      </header>
      <main className="app-main">
        <FormComponent />
      </main>
    </div>
  );
}

export default App;
