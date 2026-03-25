import {
    Button,
    Accordion,
    AccordionItem,
    AccordionHeading,
    AccordionTrigger,
    AccordionPanel,
    AccordionBody,
    Select,
    ListBox,
    ListBoxItem,
    Input,
} from "@heroui/react";
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

    return (
        <Accordion variant="default">
            <AccordionItem key="1" id="advanced-filter">
                <AccordionHeading>
                    <AccordionTrigger>Advanced Filter</AccordionTrigger>
                </AccordionHeading>

                <AccordionPanel>
                    <AccordionBody>
                        {filters.map((filter, index) => (
                            <div key={index} className="flex items-center gap-2 mt-3">
                                <Select
                                    className="w-40"
                                    value={filter.operator}
                                    onChange={(key) =>
                                        updateFilter(index, String(key ?? operators[0]), filters[index].value)
                                    }
                                    aria-label="Operator"
                                >
                                    <Select.Trigger>
                                        <Select.Value />
                                        <Select.Indicator />
                                    </Select.Trigger>

                                    <Select.Popover>
                                        <ListBox aria-label="Operator options">
                                            {operators.map((operator) => (
                                                <ListBoxItem key={operator} id={operator} textValue={operator}>
                                                    {operator}
                                                </ListBoxItem>
                                            ))}
                                        </ListBox>
                                    </Select.Popover>
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
                                    variant="secondary"
                                    onClick={() => addFilter()}
                                >
                                    <PlusIcon />
                                </Button>

                                <Button
                                    isIconOnly
                                    variant="secondary"
                                    onClick={() => removeFilter(index)}
                                >
                                    <MinusIcon />
                                </Button>
                            </div>
                        ))}
                    </AccordionBody>
                </AccordionPanel>
            </AccordionItem>
        </Accordion>
    );
}

export default AdvancedFilter;