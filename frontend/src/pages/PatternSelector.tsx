import React from 'react';
import { SignalIcon } from '@heroicons/react/24/solid';
import { PatternResult } from '../models/model';

interface PatternSelectorProps {
  patterns: PatternResult | null;
  selectedPatterns: string[];
  onPatternSelect: (patternName: string, isSelected: boolean) => void;
  showPatternSelect: boolean;
  onTogglePatternSelect: () => void;
}

const PatternSelector: React.FC<PatternSelectorProps> = ({
  patterns,
  selectedPatterns,
  onPatternSelect,
  showPatternSelect,
  onTogglePatternSelect
}) => {
  return (
    <>
      <button className="pattern-select-btn" onClick={onTogglePatternSelect}>
        <SignalIcon className="h-5 w-5" />
      </button>
      {showPatternSelect && (
        <div className="pattern-select-dropdown">
          <div className="pattern-select-title">选择K线形态</div>
          <div className="pattern-select-content">
            {patterns?.patterns ? (
              // 使用Set去除重复的形态名称
              [...new Set(patterns.patterns.map(pattern => pattern.chinese_name))].map((patternName, index) => (
                <div 
                  key={index} 
                  className={`pattern-select-item ${selectedPatterns.includes(patternName) ? 'selected' : ''}`}
                  onClick={() => {
                    const isSelected = selectedPatterns.includes(patternName);
                    onPatternSelect(patternName, !isSelected);
                  }}
                >
                  <span className="pattern-name">{patternName}</span>
                  {selectedPatterns.includes(patternName) && (
                    <span className="pattern-check">✓</span>
                  )}
                </div>
              ))
            ) : (
              <div className="pattern-select-empty">未检测到K线形态</div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default PatternSelector;