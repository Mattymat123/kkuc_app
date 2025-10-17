import { FC } from 'react';
import { Card } from 'antd';
import { CheckCircleFilled } from '@ant-design/icons';
import { TimeSlot } from './types';
import * as m from 'motion/react-m';

interface TimeSlotBoxProps {
  slot: TimeSlot;
  index: number;
  isSelected: boolean;
  onClick: () => void;
}

export const TimeSlotBox: FC<TimeSlotBoxProps> = ({ 
  slot, 
  index, 
  isSelected, 
  onClick 
}) => {
  return (
    <m.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        scale: 1.05,
        transition: { duration: 0.2 }
      }}
      transition={{ 
        duration: 0.3, 
        delay: index * 0.1,
        ease: "easeOut"
      }}
    >
      <Card
        hoverable={false}
        onClick={onClick}
        className="timeslot-card"
        style={{
          borderRadius: '12px',
          border: isSelected ? '2px solid #DF6141' : '1px solid #d9d9d9',
          backgroundColor: isSelected ? 'rgba(232, 229, 225, 0.05)' : 'white',
          cursor: 'pointer',
          position: 'relative',
          transition: 'all 0.3s ease'
        }}
        bodyStyle={{
          padding: '12px 14px',
        }}
      >
        {isSelected && (
          <CheckCircleFilled 
            style={{ 
              position: 'absolute',
              top: '10px',
              right: '12px',
              fontSize: '16px',
              color: '#DF6141'
            }} 
          />
        )}
        
        <div style={{ 
          fontSize: '14px', 
          fontWeight: 600, 
          marginBottom: '4px',
          color: 'rgba(0, 0, 0, 0.88)'
        }}>
          {slot.day}
        </div>
        
        <div style={{ 
          fontSize: '13px',
          marginBottom: '6px',
          color: 'rgba(0, 0, 0, 0.65)'
        }}>
          {slot.date}
        </div>
        
        <div style={{ 
          fontSize: '16px', 
          fontWeight: 700,
          color: '#DF6141'
        }}>
          kl. {slot.time}
        </div>
      </Card>
    </m.div>
  );
};
