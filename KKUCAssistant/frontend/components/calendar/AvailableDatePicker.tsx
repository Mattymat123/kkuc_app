'use client';

import { FC, useState } from 'react';
import { CalendarSlotsData } from './types';
import { Typography, Button, Card } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface AvailableDatePickerProps {
  data: CalendarSlotsData;
  onDateSelect?: (date: string) => void;
  selectedDate?: string | null;
}

export const AvailableDatePicker: FC<AvailableDatePickerProps> = ({ data, onDateSelect, selectedDate }) => {
  const [startDate, setStartDate] = useState(new Date());

  const nextTwoWeeks = () => {
    const newStartDate = new Date(startDate);
    newStartDate.setDate(newStartDate.getDate() + 14);
    setStartDate(newStartDate);
  };

  const prevTwoWeeks = () => {
    const newStartDate = new Date(startDate);
    newStartDate.setDate(newStartDate.getDate() - 14);
    setStartDate(newStartDate);
  };

  const renderCalendarDays = () => {
    const days = [];
    const currentDate = new Date(startDate);
    
    // Danish month names mapping
    const danishMonths: { [key: string]: number } = {
      'januar': 0, 'februar': 1, 'marts': 2, 'april': 3,
      'maj': 4, 'juni': 5, 'juli': 6, 'august': 7,
      'september': 8, 'oktober': 9, 'november': 10, 'december': 11
    };

    for (let i = 0; i < 14; i++) {
      const dateString = currentDate.toLocaleDateString('da-DK', {
        day: 'numeric',
        month: 'long'
      });

      // Check if this date has available slots
      const matchingSlot = data.slots.find(slot => {
        const slotParts = slot.date.toLowerCase().split('. ');
        if (slotParts.length === 2) {
          const slotDay = parseInt(slotParts[0]);
          const slotMonthName = slotParts[1];
          const slotMonth = danishMonths[slotMonthName];
          
          return slotDay === currentDate.getDate() && 
                 slotMonth === currentDate.getMonth();
        }
        return false;
      });

      const isAvailable = !!matchingSlot;
      const isSelected = matchingSlot && selectedDate === matchingSlot.date;

      // Extract just the day number for compact display
      const dayNumber = currentDate.getDate();
      const monthShort = currentDate.toLocaleDateString('da-DK', { month: 'short' });
      
      days.push(
        <div
          key={i}
          onClick={() => {
            if (matchingSlot && onDateSelect) {
              onDateSelect(matchingSlot.date);
            }
          }}
          style={{
            padding: '4px',
            backgroundColor: isSelected 
              ? 'rgba(223, 97, 65, 1)' 
              : isAvailable 
                ? 'rgba(223, 97, 65, 0.32)' 
                : '#f5f5f5',
            color: isSelected 
              ? 'white' 
              : isAvailable 
                ? 'rgba(0, 0, 0, 0.85)' 
                : 'rgba(0, 0, 0, 0.25)',
            borderRadius: '4px',
            cursor: isAvailable ? 'pointer' : 'not-allowed',
            fontWeight: isSelected ? '600' : '400',
            border: isSelected ? '2px solid rgba(223, 97, 65, 1)' : '1px solid #e8e8e8',
            transition: 'all 0.2s ease',
            fontSize: '11px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '40px',
            aspectRatio: '1'
          }}
          onMouseEnter={(e) => {
            if (isAvailable && !isSelected) {
              e.currentTarget.style.backgroundColor = 'rgba(223, 97, 65, 0.2)';
            }
          }}
          onMouseLeave={(e) => {
            if (isAvailable && !isSelected) {
              e.currentTarget.style.backgroundColor = 'rgba(223, 97, 65, 0.1)';
            }
          }}
        >
          <div style={{ fontSize: '14px', fontWeight: '600', lineHeight: '1' }}>{dayNumber}</div>
          <div style={{ fontSize: '9px', opacity: 0.7, marginTop: '2px' }}>{monthShort}</div>
        </div>
      );
      currentDate.setDate(currentDate.getDate() + 1);
    }
    return days;
  };

  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + 13);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'stretch',
      backgroundColor: 'transparent',
      width: '100%'
    }}>
      <Title level={4} style={{ marginBottom: '16px', color: '#DF6141' }}>
      </Title>
      <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>
      </Text>

      {/* Navigation header with Ant Design */}
      <Card 
        size="small"
        style={{
          marginBottom: '12px',
          backgroundColor: '#ffffff',
          borderColor: '#ffffff'
        }}
        bodyStyle={{
          padding: '8px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Button 
          type="text" 
          icon={<LeftOutlined />} 
          onClick={prevTwoWeeks}
          size="small"
        >
          Forrige
        </Button>

        <Text strong style={{ fontSize: '14px' }}>
          {startDate.toLocaleDateString('da-DK', { day: 'numeric', month: 'long' })} - {endDate.toLocaleDateString('da-DK', { day: 'numeric', month: 'long' })}
        </Text>

        <Button 
          type="text" 
          icon={<RightOutlined />} 
          onClick={nextTwoWeeks}
          size="small"
          iconPosition="end"
        >
          Næste
        </Button>
      </Card>

      {/* Grid of days - 7 columns x 2 rows */}
      <Card 
        size="small"
        style={{
          borderColor: '#e8e8e8'
        }}
        bodyStyle={{
          padding: '8px',
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          gap: '4px'
        }}
      >
        {renderCalendarDays()}
      </Card>

      <Text type="secondary" style={{ marginTop: '12px', textAlign: 'center', display: 'block', fontSize: '13px' }}>
        💡 Klik på en dato for at se ledige tider
      </Text>
    </div>
  );
};
