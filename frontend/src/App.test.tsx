import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders navigation links', () => {
  render(<App />);
  expect(screen.getByText(/Upload/i)).toBeInTheDocument();
  expect(screen.getByText(/Campaigns/i)).toBeInTheDocument();
  expect(screen.getByText(/Users/i)).toBeInTheDocument();
});

test('renders app logo', () => {
  render(<App />);
  expect(screen.getByText(/Revfy/i)).toBeInTheDocument();
});
