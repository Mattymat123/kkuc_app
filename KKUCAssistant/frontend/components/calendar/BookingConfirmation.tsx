'use client';

import { FC, useState } from 'react';
import { useThreadRuntime } from '@assistant-ui/react';
import { Typography, Button, Card, Checkbox, Divider } from 'antd';
import { 
  UserOutlined, 
  CalendarOutlined, 
  EnvironmentOutlined, 
  TeamOutlined, 
  FileTextOutlined,
  CheckCircleOutlined 
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface BookingConfirmationProps {
  bookingData: {
    name: string;
    phone: string;
    selectedSlot: {
      day: string;
      date: string;
      time: string;
    };
    substanceType: string;
    kommune: string;
    ageGroup: string;
    notes: string;
  };
}

const TERMS_AND_CONDITIONS = [
  'Jeg bekræfter, at de angivne oplysninger er korrekte',
  'Jeg forpligter mig til at møde op til den bookede tid',
  'Jeg vil give besked mindst 24 timer før, hvis jeg ikke kan møde op',
  'Jeg forstår, at gentagne udeblivelser kan påvirke fremtidige bookinger',
  'Jeg accepterer, at mine oplysninger behandles i henhold til GDPR'
];

export const BookingConfirmation: FC<BookingConfirmationProps> = ({ bookingData }) => {
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const threadRuntime = useThreadRuntime();

  const handleConfirmBooking = () => {
    if (!termsAccepted) return;
    
    setSubmitted(true);
    
    // Send confirmation to backend
    threadRuntime.append({
      role: 'user',
      content: [{ type: 'text', text: 'CONFIRMED' }]
    });
  };

  return (
    <div style={{ margin: '16px 0', backgroundColor: 'transparent', width: '100%' }}>
      <Card
        style={{
          borderRadius: '12px',
          borderColor: '#e8e8e8',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}
      >
        <Title level={4} style={{ marginBottom: '8px', color: '#DF6141' }}>
          Bekræft din booking
        </Title>
        <Text type="secondary" style={{ marginBottom: '24px', display: 'block' }}>
          Gennemgå venligst dine booking detaljer og acceptér vilkår og betingelser
        </Text>

        {/* Booking Details Section */}
        <div style={{
          padding: '20px',
          backgroundColor: 'rgba(223, 97, 65, 0.04)',
          borderRadius: '8px',
          marginBottom: '24px',
          border: '1px solid rgba(223, 97, 65, 0.15)'
        }}>
          <Title level={5} style={{ marginBottom: '16px', color: '#DF6141' }}>
            📋 Booking detaljer
          </Title>
          
          {/* Name */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Navn:</span>
              <span>{bookingData.name}</span>
            </Text>
          </div>

          {/* Phone */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Telefon:</span>
              <span>{bookingData.phone}</span>
            </Text>
          </div>

          {/* Date and Time */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CalendarOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Dato & Tid:</span>
              <span>{bookingData.selectedSlot.day}, {bookingData.selectedSlot.date} kl. {bookingData.selectedSlot.time}</span>
            </Text>
          </div>

          {/* Substance Type */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileTextOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Type:</span>
              <span>{bookingData.substanceType}</span>
            </Text>
          </div>

          {/* Kommune */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <EnvironmentOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Kommune:</span>
              <span>{bookingData.kommune}</span>
            </Text>
          </div>

          {/* Age Group */}
          <div style={{ marginBottom: '12px' }}>
            <Text style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TeamOutlined style={{ color: '#DF6141' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Aldersgruppe:</span>
              <span>{bookingData.ageGroup}</span>
            </Text>
          </div>

          {/* Notes */}
          <div>
            <Text style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <FileTextOutlined style={{ color: '#DF6141', marginTop: '4px' }} />
              <span style={{ fontWeight: 600, minWidth: '120px' }}>Noter:</span>
              <span style={{ flex: 1 }}>{bookingData.notes}</span>
            </Text>
          </div>
        </div>

        <Divider style={{ margin: '24px 0' }} />

        {/* Terms and Conditions Section */}
        <div style={{ marginBottom: '24px' }}>
          <Title level={5} style={{ marginBottom: '16px', color: '#DF6141' }}>
            📜 Vilkår og betingelser
          </Title>
          
          <ul style={{
            listStyle: 'none',
            padding: 0,
            margin: '0 0 20px 0'
          }}>
            {TERMS_AND_CONDITIONS.map((term, index) => (
              <li key={index} style={{
                padding: '8px 0',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px'
              }}>
                <CheckCircleOutlined style={{ color: '#52c41a', marginTop: '4px' }} />
                <Text style={{ flex: 1 }}>{term}</Text>
              </li>
            ))}
          </ul>

          <div style={{
            padding: '16px',
            backgroundColor: 'rgba(223, 97, 65, 0.08)',
            borderRadius: '8px',
            border: '1px solid rgba(223, 97, 65, 0.2)'
          }}>
            <Checkbox
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              style={{ fontSize: '15px' }}
            >
              <span style={{ fontWeight: 600, color: 'rgba(0, 0, 0, 0.85)' }}>
                Jeg accepterer alle vilkår og betingelser
              </span>
            </Checkbox>
          </div>
        </div>

        {/* Confirm Button */}
        {!submitted && (
          <div style={{
            marginTop: '24px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <Button
              type="primary"
              size="large"
              onClick={handleConfirmBooking}
              disabled={!termsAccepted}
              icon={<CheckCircleOutlined />}
              style={{
                backgroundColor: termsAccepted ? '#DF6141' : undefined,
                borderColor: termsAccepted ? '#DF6141' : undefined,
                height: '48px',
                fontSize: '16px',
                fontWeight: 600,
                borderRadius: '8px',
                paddingLeft: '40px',
                paddingRight: '40px'
              }}
            >
              Bekræft booking
            </Button>
          </div>
        )}

        {/* Helper text */}
        <Text 
          type="secondary" 
          style={{ 
            marginTop: '16px', 
            textAlign: 'center', 
            display: 'block', 
            fontSize: '13px' 
          }}
        >
          {termsAccepted 
            ? '✓ Du kan nu bekræfte din booking' 
            : '⚠️ Du skal acceptere vilkår og betingelser for at fortsætte'
          }
        </Text>
      </Card>
    </div>
  );
};
