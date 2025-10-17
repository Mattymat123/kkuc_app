'use client';

import { FC, useState } from 'react';
import { useThreadRuntime } from '@assistant-ui/react';
import { Typography, Button, Card, Select, Input, Form } from 'antd';
import { UserOutlined, PhoneOutlined, EnvironmentOutlined, TeamOutlined, FileTextOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { TextArea } = Input;

// Danish municipalities (kommuner)
const DANISH_KOMMUNER = [
  'Albertslund', 'Allerød', 'Assens', 'Ballerup', 'Billund', 'Bornholm', 'Brøndby', 'Brønderslev',
  'Dragør', 'Egedal', 'Esbjerg', 'Fanø', 'Favrskov', 'Faxe', 'Fredensborg', 'Fredericia',
  'Frederiksberg', 'Frederikshavn', 'Frederikssund', 'Furesø', 'Faaborg-Midtfyn', 'Gentofte',
  'Gladsaxe', 'Glostrup', 'Greve', 'Gribskov', 'Guldborgsund', 'Haderslev', 'Halsnæs',
  'Hedensted', 'Helsingør', 'Herlev', 'Herning', 'Hillerød', 'Hjørring', 'Høje-Taastrup',
  'Hørsholm', 'Holbæk', 'Holstebro', 'Horsens', 'Hvidovre', 'Ishøj', 'Ikast-Brande',
  'Jammerbugt', 'Kalundborg', 'Kerteminde', 'Kolding', 'København', 'Køge', 'Langeland',
  'Lejre', 'Lemvig', 'Lolland', 'Lyngby-Taarbæk', 'Læsø', 'Mariagerfjord', 'Middelfart',
  'Morsø', 'Norddjurs', 'Nordfyns', 'Nyborg', 'Næstved', 'Odder', 'Odense', 'Odsherred',
  'Randers', 'Rebild', 'Ringkøbing-Skjern', 'Ringsted', 'Roskilde', 'Rudersdal', 'Rødovre',
  'Samsø', 'Silkeborg', 'Skanderborg', 'Skive', 'Slagelse', 'Solrød', 'Sorø', 'Stevns',
  'Struer', 'Svendborg', 'Syddjurs', 'Sønderborg', 'Thisted', 'Tønder', 'Tårnby', 'Vallensbæk',
  'Varde', 'Vejen', 'Vejle', 'Vesthimmerlands', 'Viborg', 'Vordingborg', 'Ærø', 'Aabenraa',
  'Aalborg', 'Aarhus'
];

const SUBSTANCE_TYPES = [
  { label: 'Rusmiddel', value: 'Rusmiddel' },
  { label: 'Alkohol', value: 'Alkohol' },
  { label: 'Seksuelle traumer', value: 'Seksuelle traumer' }
];

const AGE_GROUPS = [
  { label: '15-24', value: '15-24' },
  { label: '25-34', value: '25-34' },
  { label: '35-44', value: '35-44' },
  { label: '45-54', value: '45-54' },
  { label: '55-64', value: '55-64' },
  { label: '65+', value: '65+' }
];

interface BookingDetailsFormProps {
  selectedSlot: {
    day: string;
    date: string;
    time: string;
  };
}

export const BookingDetailsForm: FC<BookingDetailsFormProps> = ({ selectedSlot }) => {
  const [name, setName] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [phoneError, setPhoneError] = useState<string>('');
  const [substanceType, setSubstanceType] = useState<string | null>(null);
  const [kommune, setKommune] = useState<string | null>(null);
  const [ageGroup, setAgeGroup] = useState<string | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [submitted, setSubmitted] = useState(false);
  const threadRuntime = useThreadRuntime();

  // Danish phone number validation
  const validatePhoneNumber = (phoneNum: string): boolean => {
    // Remove spaces and common separators
    const cleaned = phoneNum.replace(/[\s\-\(\)]/g, '');
    
    // Danish phone numbers: 8 digits, optionally with +45 country code
    const danishPhoneRegex = /^(\+45)?[2-9]\d{7}$/;
    
    return danishPhoneRegex.test(cleaned);
  };

  const handlePhoneChange = (value: string) => {
    setPhone(value);
    
    if (value.trim().length === 0) {
      setPhoneError('');
    } else if (!validatePhoneNumber(value)) {
      setPhoneError('Indtast et gyldigt dansk telefonnummer (8 cifre)');
    } else {
      setPhoneError('');
    }
  };

  const isFormValid = name.trim().length > 0 && 
                      phone.trim().length > 0 && 
                      phoneError === '' && 
                      validatePhoneNumber(phone) &&
                      substanceType && 
                      kommune && 
                      ageGroup;

  const handleSubmit = () => {
    if (!isFormValid) return;
    
    setSubmitted(true);
    
    // Send form data as JSON to backend
    const formData = {
      name: name.trim(),
      phone: phone.trim(),
      substanceType,
      kommune,
      ageGroup,
      notes: notes.trim()
    };
    
    threadRuntime.append({
      role: 'user',
      content: [{ type: 'text', text: JSON.stringify(formData) }]
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
          Booking detaljer
        </Title>
        <Text type="secondary" style={{ marginBottom: '24px', display: 'block' }}>
          Udfyld venligst nedenstående information for din booking
        </Text>

        {/* Selected slot info */}
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(223, 97, 65, 0.08)',
          borderRadius: '8px',
          marginBottom: '24px',
          borderLeft: '4px solid #DF6141'
        }}>
          <Text strong style={{ color: '#DF6141', fontSize: '14px' }}>
            📅 {selectedSlot.day}, {selectedSlot.date} kl. {selectedSlot.time}
          </Text>
        </div>

        {/* Form fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Name */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <UserOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Navn <span style={{ color: '#ff4d4f' }}>*</span>
            </label>
            <Input
              placeholder="Indtast dit navn (gerne anonym)"
              style={{ width: '100%' }}
              size="large"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
            />
          </div>

          {/* Phone Number */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <PhoneOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Telefonnummer <span style={{ color: '#ff4d4f' }}>*</span>
            </label>
            <Input
              placeholder="f.eks. 12345678 eller +4512345678"
              style={{ width: '100%' }}
              size="large"
              value={phone}
              onChange={(e) => handlePhoneChange(e.target.value)}
              status={phoneError ? 'error' : ''}
              maxLength={13}
            />
            {phoneError && (
              <Text type="danger" style={{ fontSize: '13px', marginTop: '4px', display: 'block' }}>
                {phoneError}
              </Text>
            )}
            {!phoneError && phone.trim().length > 0 && validatePhoneNumber(phone) && (
              <Text type="success" style={{ fontSize: '13px', marginTop: '4px', display: 'block', color: '#52c41a' }}>
                ✓ Gyldigt telefonnummer
              </Text>
            )}
          </div>

          {/* Substance Type */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <UserOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Type af substans <span style={{ color: '#ff4d4f' }}>*</span>
            </label>
            <Select
              placeholder="Vælg type"
              style={{ width: '100%' }}
              size="large"
              value={substanceType}
              onChange={setSubstanceType}
              options={SUBSTANCE_TYPES}
              getPopupContainer={(trigger) => trigger.parentElement || document.body}
              dropdownStyle={{ zIndex: 10000 }}
            />
          </div>

          {/* Kommune */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <EnvironmentOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Kommune <span style={{ color: '#ff4d4f' }}>*</span>
            </label>
            <Select
              showSearch
              placeholder="Søg eller vælg kommune"
              style={{ width: '100%' }}
              size="large"
              value={kommune}
              onChange={setKommune}
              options={DANISH_KOMMUNER.map(k => ({ label: k, value: k }))}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              getPopupContainer={(trigger) => trigger.parentElement || document.body}
              dropdownStyle={{ zIndex: 10000 }}
            />
          </div>

          {/* Age Group */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <TeamOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Aldersgruppe <span style={{ color: '#ff4d4f' }}>*</span>
            </label>
            <Select
              placeholder="Vælg aldersgruppe"
              style={{ width: '100%' }}
              size="large"
              value={ageGroup}
              onChange={setAgeGroup}
              options={AGE_GROUPS}
              getPopupContainer={(trigger) => trigger.parentElement || document.body}
              dropdownStyle={{ zIndex: 10000 }}
            />
          </div>

          {/* Notes */}
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 600,
              color: 'rgba(0, 0, 0, 0.85)'
            }}>
              <FileTextOutlined style={{ marginRight: '8px', color: '#DF6141' }} />
              Noter til visitator <span style={{ color: '#8c8c8c', fontWeight: 400 }}>(valgfri)</span>
            </label>
            <TextArea
              placeholder="Skriv dine noter her..."
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={500}
              showCount
              size="large"
              style={{ resize: 'none' }}
            />
          </div>
        </div>

        {/* Submit button */}
        {!submitted && (
          <div style={{
            marginTop: '24px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <Button
              type="primary"
              size="large"
              onClick={handleSubmit}
              disabled={!isFormValid}
              style={{
                backgroundColor: isFormValid ? '#DF6141' : undefined,
                borderColor: isFormValid ? '#DF6141' : undefined,
                height: '44px',
                fontSize: '16px',
                fontWeight: 600,
                borderRadius: '8px',
                paddingLeft: '32px',
                paddingRight: '32px'
              }}
            >
              Fortsæt til bekræftelse
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
          💡 Alle felter skal udfyldes før du kan fortsætte
        </Text>
      </Card>
    </div>
  );
};
