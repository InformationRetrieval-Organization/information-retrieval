"use client";
import { Tabs } from "@heroui/react";
import SearchComponent from "./components/SearchComponent";


export default function Home() {
  return (
    <Tabs variant="primary" aria-label="Options" className="w-full">
      <Tabs.List>
        <Tabs.Tab id="vector-space">Vector Space</Tabs.Tab>
        <Tabs.Tab id="boolean">Boolean</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel id="vector-space">
        <SearchComponent searchType="vector-space" />
      </Tabs.Panel>

      <Tabs.Panel id="boolean">
        <SearchComponent searchType="boolean" />
      </Tabs.Panel>
    </Tabs>
  );
}