import { Badge } from "@/components/ui/badge";
import { Interest } from "@/types";

interface TagRowProps {
  interests: Interest[];
}

export function TagRow({ interests }: TagRowProps) {
  if (interests.length === 0) return null;

  return (
    <div className="w-full mb-2">
      <div
        className="overflow-x-auto pb-2 scrollbar-thin"
        style={{
          overflowX: "auto",
          maxWidth: "100%",
          display: "block",
          msOverflowStyle: "auto" /* IE and Edge */,
          scrollbarWidth: "thin" /* Firefox */,
          WebkitOverflowScrolling: "touch",
        }}
      >
        <div
          className="flex items-center gap-1 whitespace-nowrap"
          style={{ paddingBottom: "4px" }}
        >
          {interests.map((interest) => (
            <Badge
              key={interest.id}
              className="whitespace-nowrap flex-shrink-0"
              style={{
                backgroundColor: `${interest.color}20`, // 20% opacity
                color: interest.color,
                borderColor: `${interest.color}30`, // 30% opacity
              }}
            >
              {interest.name}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
