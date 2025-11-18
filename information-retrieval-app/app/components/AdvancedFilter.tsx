import { Button, Accordion, AccordionItem, Select, SelectItem, Input } from "@heroui/react";
import { MinusIcon, PlusIcon } from "@/components/icons";

interface AdvancedFilterProps {
    filters: Filter[];
    setFilters: React.Dispatch<React.SetStateAction<Filter[]>>;
}

const AdvancedFilter: React.FC<AdvancedFilterProps> = ({ filters, setFilters }) => {
    const operators = ["AND", "OR", "NOT"];

    const addFilter = () => {
        setFilters([...filters, { operator: operators[0], value: "" }]);
    };

    const removeFilter = (index: number) => {
        const newFilters = [...filters];
        newFilters.splice(index, 1);
        setFilters(newFilters);
    };

    const updateFilter = (index: number, operator: string, value: string) => {
        const newFilters = [...filters];
        newFilters[index] = { operator, value };
        setFilters(newFilters);
    };

    const handleSelectionChange = (
        e: React.ChangeEvent<HTMLSelectElement>,
        index: number
    ) => {
        updateFilter(index, e.target.value, filters[index].value);
    };

    return (
        <Accordion variant="light">
            <AccordionItem key="1" aria-label="Advanced Filter" title="Advanced Filter">
                {filters.map((filter, index) => (
                    <div key={index} className="flex items-center gap-2 mt-3">
                        <Select
                            className="w-40"
                            selectedKeys={[filter.operator]}
                            onChange={(e) => handleSelectionChange(e, index)}
                            aria-label="Operator"
                        >
                            {operators.map((operator) => (
                                <SelectItem key={operator}>
                                    {operator}
                                </SelectItem>
                            ))}
                        </Select>

                        <Input
                            value={filter.value}
                            onChange={(e) =>
                                updateFilter(index, filter.operator, e.target.value)
                            }
                            placeholder="search term"
                            aria-label="Search term"
                        />

                        <Button
                            isIconOnly
                            color="primary"
                            variant="flat"
                            onClick={() => addFilter()}
                        >
                            <PlusIcon />
                        </Button>

                        <Button
                            isIconOnly
                            color="primary"
                            variant="flat"
                            onClick={() => removeFilter(index)}
                        >
                            <MinusIcon />
                        </Button>
                    </div>
                ))}
            </AccordionItem>
        </Accordion>
    );
}

export default AdvancedFilter;