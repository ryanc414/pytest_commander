/**
 * Contains InfoPane and NavBreadcrumbs components which make up the main
 * centre display pane.
 */

import React from 'react';
import { Breadcrumb, BreadcrumbItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome } from '@fortawesome/free-solid-svg-icons';
import { Link } from "react-router-dom";

import { LeafNode } from "./Common";

interface InfoPaneProps {
  selectedLeaf: LeafNode | null,
}

/**
 * InfoPane component: renders information on the currently selected testcase
 * (if any)
 * @param props Component props
 */
export const InfoPane = (props: InfoPaneProps) => {
  if (!props.selectedLeaf) {
    return <div>Please select a test.</div>
  }

  return (
    <>
      <div>{"nodeid: " + props.selectedLeaf.nodeid}</div>
      <div>{"status: " + props.selectedLeaf.status}</div>
      <div>{"longrepr: " + props.selectedLeaf.longrepr}</div>
    </>
  )
}

interface NavBreadcrumbsProps {
  selection: Array<string>
}

/**
 * Navigation breadcrumb menu, used to show the current position in the test
 * tree and to navigate back up to any parent branch node.
 * @param props Render props
 */
export const NavBreadcrumbs = (props: NavBreadcrumbsProps) => {
  const numSelected = props.selection.length;

  if (!numSelected) {
    return (
      <Breadcrumb>
        <BreadcrumbItem key="home">
          <FontAwesomeIcon icon={faHome} />
        </BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const currSelected = props.selection[numSelected - 1];
  const restSelected = props.selection.slice(0, numSelected - 1);

  return (
    <Breadcrumb>
      <BreadcrumbItem key="home">
        <Link to="/">
          <FontAwesomeIcon icon={faHome} />
        </Link>
      </BreadcrumbItem>
      {
        restSelected.map(
          (nodeid: string, index: number) => (
            <BreadcrumbItem key={nodeid}>
              <Link
                to={
                  "/" +
                  props.selection
                    .slice(0, index + 1)
                    .map(encodeURIComponent)
                    .join("/")
                }
              >
                {nodeid}
              </Link>
            </BreadcrumbItem>
          )
        )
      }
      <BreadcrumbItem>{currSelected}</BreadcrumbItem>
    </Breadcrumb>
  );
};
