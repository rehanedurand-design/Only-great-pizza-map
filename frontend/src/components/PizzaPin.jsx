// Minimalist Elegant Pizza Pin SVG Component
const PizzaPin = ({ style = "neapolitan", size = 36, className = "" }) => {
  // Color based on pizza style
  const colors = {
    neapolitan: {
      fill: "#9B2226",
      stroke: "#9B2226",
      accent: "#DDA15E"
    },
    roman: {
      fill: "#DDA15E", 
      stroke: "#BC6C25",
      accent: "#9B2226"
    }
  };

  const { fill, stroke, accent } = colors[style] || colors.neapolitan;

  return (
    <svg
      width={size}
      height={size * 1.3}
      viewBox="0 0 40 52"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Pin drop shadow */}
      <ellipse cx="20" cy="49" rx="8" ry="3" fill="rgba(0,0,0,0.15)" />
      
      {/* Main pin body - teardrop shape */}
      <path
        d="M20 0C10.06 0 2 8.06 2 18C2 31.5 20 48 20 48C20 48 38 31.5 38 18C38 8.06 29.94 0 20 0Z"
        fill={fill}
        stroke={stroke}
        strokeWidth="2"
      />
      
      {/* Inner circle - white */}
      <circle cx="20" cy="17" r="10" fill="white" />
      
      {/* Minimalist pizza slice illustration */}
      <g transform="translate(12, 9)">
        {/* Pizza triangle */}
        <path
          d="M8 0L16 14H0L8 0Z"
          fill={fill}
          opacity="0.9"
        />
        {/* Crust arc */}
        <path
          d="M0 14C0 14 4 16 8 16C12 16 16 14 16 14"
          stroke={accent}
          strokeWidth="2.5"
          strokeLinecap="round"
          fill="none"
        />
        {/* Pepperoni dots */}
        <circle cx="6" cy="8" r="1.5" fill={accent} />
        <circle cx="10" cy="10" r="1.5" fill={accent} />
        <circle cx="8" cy="5" r="1" fill={accent} />
      </g>
    </svg>
  );
};

// Alternative minimal line-art pin
export const PizzaPinMinimal = ({ style = "neapolitan", size = 36, className = "" }) => {
  const color = style === "neapolitan" ? "#9B2226" : "#BC6C25";
  
  return (
    <svg
      width={size}
      height={size * 1.2}
      viewBox="0 0 32 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Drop shadow */}
      <ellipse cx="16" cy="38" rx="6" ry="2" fill="rgba(0,0,0,0.1)" />
      
      {/* Pin outline */}
      <path
        d="M16 2C8.82 2 3 7.82 3 15C3 24 16 36 16 36C16 36 29 24 29 15C29 7.82 23.18 2 16 2Z"
        fill="white"
        stroke={color}
        strokeWidth="2"
      />
      
      {/* Simple pizza slice inside */}
      <path
        d="M16 8L22 20H10L16 8Z"
        stroke={color}
        strokeWidth="1.5"
        fill="none"
      />
      
      {/* Crust */}
      <path
        d="M10 20Q16 23 22 20"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      
      {/* Single pepperoni */}
      <circle cx="16" cy="14" r="2" fill={color} />
    </svg>
  );
};

// Even more minimal - just an elegant marker with pizza icon
export const PizzaPinElegant = ({ style = "neapolitan", size = 40, className = "" }) => {
  const color = style === "neapolitan" ? "#9B2226" : "#BC6C25";
  const bgColor = style === "neapolitan" ? "#9B2226" : "#DDA15E";
  
  return (
    <svg
      width={size}
      height={size * 1.25}
      viewBox="0 0 40 50"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' }}
    >
      {/* Elegant teardrop pin */}
      <path
        d="M20 0C9 0 0 9 0 20C0 31 20 50 20 50C20 50 40 31 40 20C40 9 31 0 20 0Z"
        fill={bgColor}
      />
      
      {/* White inner circle */}
      <circle cx="20" cy="18" r="12" fill="white" />
      
      {/* Stylized pizza icon - minimalist */}
      <g transform="translate(11, 9)">
        {/* Pizza slice triangle */}
        <path
          d="M9 2L17 16H1L9 2Z"
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        {/* Curved crust */}
        <path
          d="M1 16Q9 19 17 16"
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Toppings - elegant dots */}
        <circle cx="7" cy="10" r="1.5" fill={color} />
        <circle cx="11" cy="12" r="1.5" fill={color} />
        <circle cx="9" cy="7" r="1" fill={color} />
      </g>
    </svg>
  );
};

export default PizzaPin;
