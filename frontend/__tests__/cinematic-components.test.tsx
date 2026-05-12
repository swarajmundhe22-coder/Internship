import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AtmosphericParticles } from '../components/AtmosphericParticles';
import { CinematicVideoOverlay } from '../components/CinematicVideoOverlay';
import { Explainability3DGraph } from '../components/Explainability3DGraph';
import Act0Briefing from '../components/outsource/local-simulated/components/Act0Briefing';
import { Canvas } from '@react-three/fiber';

// Mock Three.js and related components
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useFrame: jest.fn(),
  useThree: jest.fn(() => ({ camera: {}, scene: {} })),
}));

jest.mock('@react-three/drei', () => ({
  Points: ({ children }: { children: React.ReactNode }) => <div data-testid="points">{children}</div>,
  PointMaterial: () => <div data-testid="point-material" />,
  Sphere: ({ children }: { children: React.ReactNode }) => <div data-testid="sphere">{children}</div>,
  Line: () => <div data-testid="line" />,
  Text: ({ children }: { children: React.ReactNode }) => <div data-testid="text">{children}</div>,
  Float: ({ children }: { children: React.ReactNode }) => <div data-testid="float">{children}</div>,
  Stars: () => <div data-testid="stars" />,
  MeshDistortMaterial: () => <div data-testid="mesh-distort-material" />,
}));

jest.mock('framer-motion', () => ({
  ...jest.requireActual('framer-motion'),
  useScroll: () => ({ scrollYProgress: { get: () => 0, onChange: jest.fn() } }),
  useTransform: () => 0,
}));

describe('Cinematic Components Audit', () => {
  test('AtmosphericParticles renders correctly', () => {
    const { getByTestId } = render(
      <Canvas>
        <AtmosphericParticles count={1000} color="#00e5ff" />
      </Canvas>
    );
    expect(getByTestId('points')).toBeInTheDocument();
  });

  test('CinematicVideoOverlay triggers correctly on low confidence', () => {
    const { container, rerender } = render(
      <CinematicVideoOverlay 
        src="test.mp4" 
        triggeredByConfidence={0.95} 
        threshold={0.9} 
      />
    );
    // Should not be active at high confidence
    expect(container.querySelector('video')).not.toBeInTheDocument();

    rerender(
      <CinematicVideoOverlay 
        src="test.mp4" 
        triggeredByConfidence={0.85} 
        threshold={0.9} 
      />
    );
    // Should be active at low confidence
    expect(container.querySelector('video')).toBeInTheDocument();
  });

  test('Explainability3DGraph renders with nodes', () => {
    const testData = [
      { name: "Test Node", impact: 0.5, category: "Environment" }
    ];
    const { getAllByTestId } = render(
      <Canvas>
        <Explainability3DGraph data={testData} />
      </Canvas>
    );
    // Central node + test node
    expect(getAllByTestId('sphere').length).toBeGreaterThanOrEqual(2);
  });

  test('Act0Briefing renders with cinematic elements', () => {
    const { getByText, getByTestId } = render(
      <Act0Briefing onStart={() => {}} />
    );
    expect(getByText(/Silent/i)).toBeInTheDocument();
    expect(getByText(/Decay/i)).toBeInTheDocument();
    expect(getByTestId('stars')).toBeInTheDocument();
  });
});
