import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";

export default function PaymentsView() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="">
          <Title text="Financial Overview" />
          <Text text="Manage payments, track debts, and view financial history." />
        </div>
      </div>
    </div>
  )
}
