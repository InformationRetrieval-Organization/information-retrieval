"use client";
import { Tabs, Tab } from "@heroui/react";
import SearchComponent from "./components/SearchComponent";


export default function Home() {
  return (
    <Tabs color="primary"
      variant="underlined"
      size="lg"
      aria-label="Options"
      fullWidth>
      <Tab key="vector-space" title="Vector Space">
        <SearchComponent searchType="vector-space" />
      </Tab>
      <Tab key="boolean" title="Boolean">
        <SearchComponent searchType="boolean" />
      </Tab>
    </Tabs>
  );
}