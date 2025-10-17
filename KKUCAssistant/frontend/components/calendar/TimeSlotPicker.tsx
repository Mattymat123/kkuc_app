'use client';

import { FC, useState, useMemo } from 'react';
import { useThreadRuntime } from '@assistant-ui/react';
import { Typography, Button, Card, List } from 'antd';
import { ClockCircleOutlined, CalendarOutlined } from '@ant-design/icons';
import { CalendarSlotsData } from './types';
import { TimeSlotBox } from './TimeSlotBox';
import { AvailableDatePicker } from './AvailableDatePicker';

const { Title, Text } = Typography;

interface TimeSlotPickerProps {
  data: CalendarSlotsData;
}

export const TimeSlotPicker: FC<TimeSlotPickerProps> = ({ data }) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  // Default to the first available date
  const [selectedDate, setSelectedDate] = useState<string | null>(
    data.slots.length > 0 ? data.slots[0].date : null
  );
  const [confirmedSelection, setConfirmedSelection] = useState(false);
  const threadRuntime = useThreadRuntime();

  const handleSlotClick = (index: number) => {
    // Toggle selection - if clicking the same slot, deselect it
    setSelectedIndex(prevIndex => prevIndex === index ? null : index);
  };

  const handleConfirmSelection = () => {
    if (selectedIndex !== null) {
      setConfirmedSelection(true);
      // Send the slot number (1-based) to the backend
      const slotNumber = (selectedIndex + 1).toString();
      threadRuntime.append({
        role: 'user',
        content: [{ type: 'text', text: slotNumber }]
      });
    }
  };

  const handleDateClick = (date: string) => {
    // Toggle selection - if clicking the same date, unselect it
    setSelectedDate(prevDate => prevDate === date ? null : date);
  };

  // Filter slots based on selected date
  const filteredSlots = useMemo(() => {
    if (!selectedDate) return data.slots;
    return data.slots.filter(slot => slot.date === selectedDate);
  }, [data.slots, selectedDate]);

  // Group slots by date, then separate into morning/afternoon
  const groupedSlots = useMemo(() => {
    const groups: { [date: string]: { day: string; morning: typeof filteredSlots; afternoon: typeof filteredSlots } } = {};
    
    filteredSlots.forEach(slot => {
      if (!groups[slot.date]) {
        groups[slot.date] = {
          day: slot.day,
          morning: [],
          afternoon: []
        };
      }
      
      const hour = parseInt(slot.time.split(':')[0]);
      if (hour < 12) {
        groups[slot.date].morning.push(slot);
      } else {
        groups[slot.date].afternoon.push(slot);
      }
    });
    
    return Object.entries(groups).map(([date, data]) => ({
      date,
      day: data.day,
      morning: data.morning,
      afternoon: data.afternoon
    }));
  }, [filteredSlots]);

  return (
    <div style={{ margin: '16px 0', backgroundColor: 'transparent', width: '100%' }}>
      {/* Calendar on top */}
      <AvailableDatePicker 
        data={data} 
        onDateSelect={handleDateClick}
        selectedDate={selectedDate}
      />

      {/* Time slots below */}
      <div style={{ marginTop: '16px' }}>
        <Title level={4} style={{ marginBottom: '8px', color: '#DF6141' }}>
        </Title>
        <Text type="secondary" style={{ marginBottom: '16px', display: 'block' }}>
        </Text>
        
        {/* Grouped by date with two-column grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '16px' }}>
          {groupedSlots.map((group, groupIndex) => (
            <div key={groupIndex}>
              {/* Date header */}
              <div style={{
                padding: '8px 12px',
                backgroundColor: '#DF6141',
                color: 'white',
                borderRadius: '8px 8px 0 0',
                fontWeight: 600,
                fontSize: '14px'
              }}>
                {group.day}
              </div>
              
              <div style={{ position: 'relative' }}>
                <Card 
                  size="small"
                  style={{
                    overflow: 'hidden',
                    borderTopLeftRadius: 0,
                    borderTopRightRadius: 0,
                    maxHeight: '20vh',
                    paddingBottom: '0px'
                  }}
                  bodyStyle={{ padding: 0 }}
                >
                  {/* Column headers */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1px',
                    backgroundColor: '#ffffff',
                  }}>
                    <div style={{
                      padding: '8px 12px',
                      backgroundColor: 'white',
                    }}>
                      <Text style={{ margin: 0, color: '#DF6141', fontSize: '13px', fontWeight: 600 }}>
                        Formiddag
                      </Text>
                    </div>
                    <div style={{
                      padding: '8px 12px',
                      backgroundColor: 'white'
                    }}>
                      <Text style={{ margin: 0, color: '#DF6141', fontSize: '13px', fontWeight: 600 }}>
                        Eftermiddag
                      </Text>
                    </div>
                  </div>

                  {/* Scrollable content with two columns - max 3-4 visible items */}
                  <div style={{
                    maxHeight: '180px',
                    overflowY: 'auto',
                    overflowX: 'hidden',
                    scrollBehavior: 'smooth'
                  }}>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '1px',
                      backgroundColor: '#ffffff'
                    }}>
                      {/* Morning column */}
                      <div style={{ backgroundColor: 'white' }}>
                        {group.morning.length > 0 ? (
                          group.morning.map((slot) => {
                            const slotIndex = data.slots.indexOf(slot);
                            const isSelected = selectedIndex === slotIndex;
                            return (
                              <div
                                key={slotIndex}
                                onClick={() => handleSlotClick(slotIndex)}
                                style={{
                                  padding: '10px 12px',
                                  cursor: 'pointer',
                                  backgroundColor: isSelected ? 'rgba(223, 97, 65, 0.05)' : 'transparent',
                                  borderLeft: isSelected ? '3px solid #DF6141' : '3px solid transparent',
                                  transition: 'all 0.3s ease',
                                }}
                              >
                                <div style={{
                                  padding: '6px 10px',
                                  backgroundColor: isSelected ? '#DF6141' : '#ffffff',
                                  color: isSelected ? 'white' : 'rgba(0, 0, 0, 0.85)',
                                  borderRadius: '6px',
                                  fontWeight: 600,
                                  fontSize: '14px',
                                  transition: 'all 0.3s ease',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px'
                                }}>
                                  <ClockCircleOutlined style={{ fontSize: '18px' }} />
                                  {slot.time}
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div style={{ 
                            padding: '24px 12px', 
                            textAlign: 'center', 
                            color: 'rgba(0, 0, 0, 0.45)',
                            fontSize: '12px'
                          }}>
                            Ingen ledige tider
                          </div>
                        )}
                      </div>

                      {/* Afternoon column */}
                      <div style={{ backgroundColor: 'white', borderLeft: '1px solid #f0f0f0' }}>
                        {group.afternoon.length > 0 ? (
                          group.afternoon.map((slot) => {
                            const slotIndex = data.slots.indexOf(slot);
                            const isSelected = selectedIndex === slotIndex;
                            return (
                              <div
                                key={slotIndex}
                                onClick={() => handleSlotClick(slotIndex)}
                                style={{
                                  padding: '10px 12px',
                                  cursor: 'pointer',
                                  backgroundColor: isSelected ? 'rgba(223, 97, 65, 0.05)' : 'transparent',
                                  borderLeft: isSelected ? '3px solid #DF6141' : '3px solid transparent',
                                  transition: 'all 0.3s ease',
                                }}
                              >
                                <div style={{
                                  padding: '6px 10px',
                                  backgroundColor: isSelected ? '#DF6141' : '#ffffff',
                                  color: isSelected ? 'white' : 'rgba(0, 0, 0, 0.85)',
                                  borderRadius: '6px',
                                  fontWeight: 600,
                                  fontSize: '14px',
                                  transition: 'all 0.3s ease',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px'
                                }}>
                                  <ClockCircleOutlined style={{ fontSize: '18px' }} />
                                  {slot.time}
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div style={{ 
                            padding: '24px 12px', 
                            textAlign: 'center', 
                            color: 'rgba(0, 0, 0, 0.45)',
                            fontSize: '12px'
                          }}>
                            Ingen ledige tider
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
                
                {/* Gradient fade effect at bottom */}
                {(group.morning.length > 4 || group.afternoon.length > 4) && (
                  <div style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '40px',
                    background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.95) 100%)',
                    pointerEvents: 'none',
                    borderBottomLeftRadius: '8px',
                    borderBottomRightRadius: '8px'
                  }} />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Confirm button - shown when a slot is selected */}
        {selectedIndex !== null && !confirmedSelection && (
          <div style={{
            marginTop: '16px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <Button
              type="primary"
              size="large"
              onClick={handleConfirmSelection}
              style={{
                backgroundColor: '#DF6141',
                borderColor: '#DF6141',
                height: '44px',
                fontSize: '16px',
                fontWeight: 600,
                borderRadius: '8px',
                paddingLeft: '32px',
                paddingRight: '32px'
              }}
            >
              Bekræft valg
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
